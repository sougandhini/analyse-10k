import os 
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
HEADERS = {"User-Agent": os.environ["SEC_USER_AGENT"]}
# why caps? coz this is a constant 

# Notice _get: means internal helper function (protected kind) so dont use it outside this file 
def _get(url:str) -> requests.Response:
    response = requests.get(url, headers=HEADERS, timeout=30)
    # timeout=30 means “give up after 30 seconds.” Without it, requests can wait forever on a stuck connection and hang your program
    response.raise_for_status()
    # if the status code indicates failure (4xx or 5xx), this raises an exception. Failing right here makes the real cause obvious.
    return response

# ticker is a SHORTCODE for a company's shares trade on a stock exchange

# this function gets the permanent fixed id (cik) of a company from its ticker
def get_cik(ticker: str) ->str:
    data = _get("https://www.sec.gov/files/company_tickers.json").json()
    # the keys are just 0,1,2 so we are interested only in values
    for entry in data.values():
        if entry["ticker"].lower() == ticker.lower():
            # hey access the cik_str it comes in int format, we want it to have 10 digits, so convert to str and zfill with 0's to LEFT till the entire string has 10 digits eg. cik:12345 it'll be 0000012345
            return str(entry["cik_str"]).zfill(10)
        
    raise ValueError(f"Ticker {ticker} not found")


def list_10ks(cik:str) -> list[dict]:
    data = _get(f"https://data.sec.gov/submissions/CIK{cik}.json").json()
    recent = data["filings"]["recent"]
    filings = []
    for form, accession, document, report_date, filing_date in zip(
        recent["form"],
        recent["accessionNumber"],
        recent["primaryDocument"],
        recent["reportDate"],
        recent["filingDate"],
        strict=True
    ):
        if form=="10-K":
            url = (
                f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"f"{accession.replace('-','')}/{document}"
            )
            filings.append(
                {
                    "report_date":report_date, "filing_date":filing_date,
                    "url":url
                }
            )
    return filings

def download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    # makes the folder (like data/) if it doesn’t exist. parents=True also creates missing parent folders and exist_ok=True means no error if it’s already there
    dest.write_bytes(_get(url).content)
    # .content is the raw bytes of the response (as opposed to .text, which is decoded text). Saving raw bytes preserves the file exactly as the SEC sent it, avoiding any character-encoding surprises. write_bytes writes them to the file, so we didn't convert it into .text
    return dest

if __name__=="__main__":
    cik = get_cik("TSLA")
    print("CIK: ", cik)
    for file in list_10ks(cik):
        print(file["report_date"], file["filing_date"], file["url"])
        
    # next(...) is how you ask a generator for its first match item
    target = next(file for file in list_10ks(cik) if file["report_date"].startswith("2025"))
    path = download(target["url"], Path("data/tesla_10k_2025.htm"))
    print("Saved", path, path.stat().st_size, "bytes")
    