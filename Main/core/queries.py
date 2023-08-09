import json
import openai


def get_raw(msg, attachment_data):
    RAW = {
        "Sender": msg.sender,
        "Date": msg.date,
        "Subject": msg.subject,
        "Content": msg.body,
        "Attachment_data": attachment_data
    }
    return RAW


def parse_document(BaseData, pdf_output):
    messages = [{"role": "system", "content": "You are an email parser that deals with insurance companies."}]
    prompt = f"Fill the following dictionary with the appropriate values from the following data. adjust the format as you see fit. \n" \
             f"the information filled should be straight forward and not large chunks from the text data or symbols such as end of line statements. \n" \
             f"The output should be in json format since it will need to be loaded afterwards. \n" \
             f"Dictionary: \n {json.dumps(BaseData)} \n" \
             f"Data: \n {str(pdf_output)} \n"

    messages.append({"role": "user", "content": prompt})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=messages,
        temperature=0
    )
    # make sure response is in the form of dict
    updated_data = []
    answer = ""
    try:
        for choice in response.choices:
            answer += choice.message.content
        updated_data = json.loads(answer)
    except Exception as e:
        updated_data = {
            "response": answer,
            "Errors": [f"{e}"]}
        print("Couldn't load response.")

    # return updated Data
    return updated_data


def get_output_format():
    # Property Coverage (for every location)
    property_coverage = {
        "Location address": "",
        "Building limit": "",
        "Contents limit": "",
        "Equipment limit": "",
        "Stock limit": "",
        "Rental Income": "",
        "Business Interruption limit": "",
        "Year built": "",
        "Type of construction": "",
        "Type of Roof": "",
        "The year of last update/ renovation to building , HVAC, plumbing and electrical": "",
        "Square footage": "",
        "Number of Stories": "",
        "Occupied by insured as": "",
        "Adjacent exposure": "",
        "Mortgagee details – Name and Address": ""
    }

    # Liability Coverage
    liability_coverage = {
        "Limit required": {
            "Bodily Injury Property Damage Limit": "",
            "Personal Advertising Injury Limit": "",
            "Tenant's Legal Liability Limit": "",
            "Non Owned Automobile Deductible": "",
        },
        "Annual revenue": "",
        "Revenue split – US, Canada and others": "",
        "Liquor receipts": "",
        "Liquor percent": "",
        "Location details – address of all": ""
    }
    # CEF Coverage
    CEF_coverage = {
        "equipments": [
            {
                "Make": "",
                "Model": "",
                "Serial Number": "",
                "Limit": "",
                "Mortgage Name and Address": ""
            }
        ],
        "professional_liability": [
            {
                "Expiring Professional Liability Limit": "",
                "Proposed Professional Liability Limit": "",
                "Annual revenue last 12 month": "",
                "Annual revenue last 12 monthLiability": "",
                "Number of Employees": "",
                "Location details – address of all": ""
            },
        ],
        "directors_and_officers": [
            {
                "Date of incorporation": "",
                "Number of Employee": "",
                "Jurisdiction of incorporation": "",
                "Entity percent of ownership": "",
                "Assets": "",
                "Liability": "",
                "Revenue": "",
                "Net Income": ""
            },
        ],
        "builders_risk": [
            {
                "Construction Start and End date": "",
                "Project Value": "",
                "Location": "",
                "Description of work": "",
                "Number of stories": "",
                "Construction": "",
                "Roof": "",
                "Liability Limit": "",
            },
        ],
    }

    Data = {
        "Insured Name": ""
        ,
        "Mailing address": ""
        ,
        "Date the submission is received ": ""
        ,
        "Policy Inception and Policy Expiry Date": ""
        ,
        "Broker’s name and contact information  ": ""
        ,
        "Description of Operations": ""
        ,
        "property_coverage": property_coverage
        ,
        "liability_coverage": liability_coverage
        ,
        "CEF_coverage": CEF_coverage
    }
    return Data


def merge(val1, val2):
    if isinstance(val1, dict):
        for key, item in val1.items():
            if key in val2:
                merge(val1[key], val2[key])
    if isinstance(val1, list):
        if isinstance(val2, list):
            val1.extend(val2)
    if isinstance(val1, str):
        if val1 in ["", " ", "NaN", "N/A"] and isinstance(val2, str):
            val1 = val2
