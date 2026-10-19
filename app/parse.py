import re
from pathlib import Path

from bs4 import BeautifulSoup

# Block tags start new lines in browser
BLOCK_TAGS = ["p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6"]

# represent table's cell
# td: table data cell (1 cell); tr - table row and th - table header cell
# <table>
#   <tr><th>Item</th><th>2025</th></tr>
#   <tr><td>Revenue</td><td>97,690</td></tr>
# </table>
CELL_TAGS = ["td", "th"]

# Sample: Item 10A - Risk Factors
HEADING = re.compile(
    r"^ *item +(\d{1,2}[A-C]?) *[.:\-–—]? *(.*)$",re.IGNORECASE | re.MULTILINE 
)

def html_to_text(path: Path) -> str:
    soup = BeautifulSoup(path.read_bytes(), "html.parser")
    # this html.parser is python's inbuilt parser
    
    # cleaning the html

    for tag in soup.find_all(["ix:header", "script", "style"]):
        # delete the tag and everything inside it, coz nothing is readable financial data
        tag.decompose()
    
    
    for tag in soup.find_all(BLOCK_TAGS):
        tag.insert_after("\n")
        
    for tag in soup.find_all(CELL_TAGS):
        tag.insert_after(" ")
    
    text = soup.get_text() # extracts all the text from the entire document, we've already defined the layout by adding \n and " ", so no issues now
    
    
    # wierd white space
    text = text.replace("\xa0", " ")
    
    # wherever there's tab or series of whitespaces, replace it with whitespace
    # find all and replace (re.sub(pattern, replacement, where_to_replace))
    text = re.sub(r"[ \t]+", " ", text)
    
    # take text, and for each line you strip all the spaces, and add only one space at the end
    text = "\n".join(line.strip() for line in text.splitlines())
    
    
    # collapses three or more newlines in a row into one blank line.
    text = re.sub(r"\n{3,}","\n\n", text)
    
    return text.strip()


# (match.group(0) = 'Item 1A. Risk Factors', match.group(1) = '1A', match.group(2) = 'Risk Factors')
def find_headings(text: str) -> list[dict]:
    headings = []
    for match in HEADING.finditer(text):
        line = match.group(0).strip()
        if len(line) > 150:
            continue
        headings.append(
            {"item": match.group(1).upper(), "start": match.start(), "line":line}
            
            # item : 1A
            # start : index where matching of heading pattern starts
            # line: Item 1A. Risk Factors
        )
    return headings

def split_sections(text: str) -> dict[str, str]:
    headings = find_headings(text)
    
    # best is the name of a dict, and the dict is expected to store string keys and string values
    best: dict[str, str] = {}
    for index, heading in enumerate(headings):
        
        # the current section ends at the beginning of the next section
        if index+1 < len(headings):
            end = headings[index+1]["start"]
        else: 
            end = len(text)
        
        # extract section out of text
        section = text[heading["start"]:end]
        item = heading["item"]
        
        # if this item 1A not present in my section_list best or my present length of that key < than the incoming one, then replace it
        
        # this says how we loose table of contents line... choose that section whose subsequent characters are longer
        if item not in best or len(section) > len(best[item]):
            best[item] = section
            
    return best
    

if __name__ == "__main__":
    src = Path("data/tesla_10k_2025.htm")
    
    # cleaned html
    text = html_to_text(src)
    
    src.with_suffix(".txt").write_text(text, encoding="utf-8")
    print("Characters of clean text: ", len(text))
    
    print("\nALL headings found: ")
    for heading in find_headings(text):
        # heading["start"]:>9 means right-align the text in 9 characters
        print(f'start: {heading["start"]:>9} Item: {heading["item"]:<4} Full Name: {heading["line"][:70]}')
    
    sections = split_sections(text)
    print("\nChosen sections: ")
    for item, body in sections.items():
        # len(body):>9 - means add thousands separator
        print(f"Item in section: {item:<4} {len(body):>9,} chars")

    