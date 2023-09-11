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


def parse_document(BaseData, curr_data, pdf_output):
    messages = [{"role": "system", "content": "You are an email parser that deals with insurance companies."}]
    prompt = f"Fill the following dictionary with the appropriate values from the following data. adjust the format as you see fit. \n" \
             f"the information filled should be straight forward and not large chunks from the text data or symbols such as end of line statements. \n" \
             f"The output should be in json format since it will need to be loaded afterwards. \n" \
             f"Dictionary base format: \n {json.dumps(BaseData)} \n" \
             f"{get_coverage_formats()} \n" \
             f"Dictionary current extracted data: \n {json.dumps(curr_data)} \n" \
             f"new Data: \n {str(pdf_output)} \n"

    messages.append({"role": "user", "content": prompt})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
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


def get_coverage_formats():
    # Property Coverage (for every location)
    property_coverage = {
        "Type": "propery coverage",
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
        "The year of last update(renovation to building , HVAC, plumbing and electrical)": "",
        "Square footage": "",
        "Number of Stories": "",
        "Occupied by insured as": "",
        "Adjacent exposure": "",
        "Mortgagee details": {"name": "",
                              "address": ""}
    }

    # Liability Coverage
    liability_coverage = {
        "Type": "liability coverage",
        "Limit required": {
            "Bodily Injury Property Damage Limit": "",
            "Personal Advertising Injury Limit": "",
            "Tenant's Legal Liability Limit": "",
            "Non Owned Automobile Deductible": "",
        },
        "Annual revenue": "",
        "Revenue split": "",
        "Liquor receipts": "",
        "Liquor percent": "",
        "Location details": ""
    }
    # CEF Coverage
    CEF_coverage = {
        "Type": "CEF coverage",
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
                "Annual revenue last 12 month Liability": "",
                "Number of Employees": "",
                "Location details": ""
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

    output = f"For the coverage field it will depend on the coverage type. if it's a property coverage, the format will be as follows: \n {json.dumps(property_coverage)} \n" \
             f" if it's a liability coverage, the format will be as follows: \n {json.dumps(liability_coverage)} \n" \
             f" if it's a CEF coverage, the format will be as follows: \n {json.dumps(CEF_coverage)} \n" \
             "The empty fields of the dictionaries need to be filled or omitted otherwise. this also applies for the nested fields.\n"
    return output


def get_output_format():
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
        "Coverage": []
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
