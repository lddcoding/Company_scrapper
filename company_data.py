import json
import requests
import pandas as pd
import streamlit as st
from pydantic import BaseModel

class AnswerFormat(BaseModel):
    Company_website: str
    Industry: str
    Company_Description: str
    Company_Achievements: str
    Nb_full_time_employee: str
    Headquarters: str
    Sector: str
    Industry_Group: str
    Industry: str
    Sub_Group: str
    Management_1: str
    Management_2: str
    Management_3: str

with open('GICS.json', 'r') as file:
    gics_structure = json.load(file)

gics_structure_str = json.dumps(gics_structure)

def get_linkedin_company_info(company_name):
    
    ACCESS_TOKEN = "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"
    LINKEDIN_API_URL = "https://api.linkedin.com/v2/organizations"
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }

    search_url = f"https://api.linkedin.com/v2/organizationAcls?q=organization&organization={company_name}"
    search_response = requests.get(search_url, headers=headers)
    
    if search_response.status_code == 200:
        data = search_response.json()
        if "elements" in data and len(data["elements"]) > 0:
            company_id = data["elements"][0]["organization"]  # Extract Company ID
            
            # Fetch company details using the company ID
            company_url = f"{LINKEDIN_API_URL}/{company_id}"
            response = requests.get(company_url, headers=headers)
            
            if response.status_code == 200:
                return response.json()  # Returns the company page content
            else:
                return {"error": f"Failed to retrieve company data: {response.status_code}"}
        else:
            return {"error": "Company not found"}
    else:
        return {"error": f"Search request failed: {search_response.status_code}"}

def find_company_website(company_name, api_key):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": company_name,
        "key": api_key,
        "cx": "845c0833a412b4955",  
        "num": 1 
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if "items" in data and len(data["items"]) > 0:
            return data["items"][0]["link"]
        else:
            return None
    
    except requests.exceptions.RequestException as e:
        print(f"Error while searching for company website: {e}")
        return None
        
def get_company_info_and_classify(company_name: str, location: str):
    url = "https://api.perplexity.ai/chat/completions"
    headers = {"Authorization": "Bearer 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"}

    # Prepare the payload with company info and GICS structure
    payload = {
        "model": "sonar-pro",
        "messages": [
            {"role": "system", "content": "Be an expert in business"},
            {"role": "user", "content": (
                f"Make research on {company_name} based in {location}. "
                "(only output the JSON object and don't put any JSON text or line break) "
                "For the headquarters, only put the city, and put an exhaustive business description for the business. "
                "For company achievements put some key facts about the company that would be interesting, such as activities in other places, certification, investors in the company (private equity investment), etc. But don't put anything that is already mentioned in the business description. "
                "For the different management inputs, find some key management person within the company such as CEO, CFO, CTO, CIO, etc, or other important member of the organisation"
                f"Classify the business based on the following GICS structure: {gics_structure_str}. "
                "Please output a JSON object containing the following fields: "
                "Company_website, Company_Description, Company_Achievements, Nb_full_time_employee, Headquarters, "
                "Sector, Industry Group, Industry, Sub-Industry, Management_1, Management_2, Management_3."
            )},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"schema": AnswerFormat.model_json_schema()},
        },
    }

    # Send the request to Perplexity API
    response = requests.post(url, headers=headers, json=payload).json()

    # Extract and return the company data
    json_response = response["choices"][0]["message"]["content"]
    company_data = json.loads(json_response)
    return company_data

st.title("Company Info and Classification Tool")

company_input = st.text_area("Enter Company Names and Locations (one per line, format: Company Name, Location)")

if st.button("Get Company Info"):
    if company_input:
        companies = company_input.split('\n')
        data = []

        # Process each company
        for company in companies:
            try:
                company_name, location = company.split(',')
                company_name = company_name.strip()
                location = location.strip()

                company_info = get_company_info_and_classify(company_name, location)
                data.append(company_info)
            except Exception as e:
                st.error(f"Error processing {company}: {e}")

        if data:
            df = pd.DataFrame(data)
            st.dataframe(df)
    else:
        st.error("Please enter the company names and locations.")
