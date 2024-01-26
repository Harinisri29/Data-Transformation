import json
from datetime import datetime
from dateutil.tz import tzutc
import re
import time

mandatory_fields     = ["Category_Name", "Category_ID", "Sub_Category_Name", "Sub_Category_ID",
                        "Grade", "Grade_ID", "Grade_Type", "Grade_Type_ID",
                        "Region", "Region_ID", "Currency", "Unit", "Period", "Actual_Period", "Price_Point"]
date_fields          = ["Actual_Period"]
numerical_fields     = ["Percentage_Change", "Price_Point", "Accuracy_3_months", "Accuracy_6_months",
                        "Accuracy_12_months", "Supply_Demand_Gap_Current", "Supply_Demand_Gap_Short_Term",
                        "Supply_Demand_Gap_Medium_Term", "Supply_Demand_Gap_Long_Term", "Trade_Balance",
                        "Utilization_Operating_Rates_Percentage", "Input_Costs_Percentage", "Profitability_Percentage"]
trend_fields_current = ["Supply_Trend_Current", "Demand_Trend_Current", "Feedstock_Trend_Current"]
id_fields_check      = ["Sub_Category_ID", "Region_ID", "Grade_ID"]
id_check             = [("Feedstock", "Feedstock_ID"),("Substitute", "Substitute_ID"),("Related_Sub_Category", "Related_Sub_Category_ID")]
trend_fields         = ["Supply_Trend_Current", "Demand_Trend_Current", "Feedstock_Trend_Current",
                        "Price_Trend_Current", "Supply_Trend_Short_Term", "Demand_Trend_Short_Term",
                        "Feedstock_Trend_Short_Term", "Price_Trend_Short_Term", "Supply_Trend_Medium_Term",
                        "Demand_Trend_Medium_Term", "Feedstock_Trend_Medium_Term", "Price_Trend_Medium_Term",
                        "Supply_Trend_Long_Term", "Demand_Trend_Long_Term", "Feedstock_Trend_Long_Term",
                        "Price_Trend_Long_Term", "Labor_Laws_Hours_of_work", "Labor_Laws_Labor_Supply",
                        "Labor_Laws_Cost_of_Labor"]


def validate_data(input_data):
    result = []
    sub_category_pattern = re.compile(r'^[A-Z]\d{3}$')
    region_pattern = re.compile(r'^REG-\d{4}$')
    grade_pattern = re.compile(r'^[A-Z]\d{3}-\d{2}$')
    comma_separated_pattern = re.compile(r'^[A-Z]\d{3}(,[A-Z]\d{3})*$')

    for item in input_data:
        output_data_entry = {
            'errors': {
                'mandatory_fields': [],
                'id_field_check': [],
                'id_check': [],
                'numerical_fields': [],
                'date_fields': [],
                'trend_fields': []
            }
        }

        # Check Numerical Fields         
        for field in numerical_fields:
            if field not in item or (item[field] != "" and not re.match(r'^[-+]?\d*\.?\d+%?$', str(item[field]))):
                output_data_entry['errors']['numerical_fields'].append(field)

        # Check Date Fields      
        for field in date_fields:
            if field not in item :
                output_data_entry['errors']['date_fields'].append(field)
            else:
                actual_period_value = item[field] 
                period_value = item.get("Period", "")

                # Check format based on Period
                if period_value == "Monthly" and re.match(r'^[A-Za-z]{3}-\d{4}$', actual_period_value):
                    continue
                elif period_value == "Quarterly" and re.match(r'^Q[1-4] \d{4}$', actual_period_value):
                    continue
                elif period_value == "Annual" and re.match(r'^\d{4}$', actual_period_value):
                    continue
                else:
                    output_data_entry['errors']['date_fields'].append(field)

        # ID Fields Check
        for field in id_fields_check:
            if field not in item :
                output_data_entry['errors']['id_field_check'].append(field)

        # ID check
        for field, id_field in id_check:
            if field in item and id_field in item and not item[field] and not item[id_field]:
                # Both values are present and empty-----so not an issue
                continue

            elif field in item and id_field in item and item[field] and item[id_field]:
                # Both values are present, check if they match the comma-separated pattern
                if not comma_separated_pattern.match(item[id_field]):
                    output_data_entry['errors']['id_check'].append(id_field)
            
            elif (field in item and not item[id_field]) or (id_field in item and not item[field]):
                # Only one of the fields is present----append the missing one
                missing_field = id_field if not item[id_field] else field
                output_data_entry['errors']['id_check'].append(missing_field)

        # Trend Fields
        for field in trend_fields:
            if field not in item :
                output_data_entry['errors']['trend_fields'].append(field)

            elif field in trend_fields:
                if item[field]=="" :
                    continue
                field_value = item[field]
                valid_field_value = ["Decreasing", "Increasing", "Stable", "Steady"]
                
                if field in trend_fields_current:
                    # Extract values for the specific trend fields
                    values = [part.strip() for part in field_value.split(';')]                    
                    for value in values:                        
                        if value:
                            category, trend_part = value.split(':')
                            #category = category.strip()
                            trend_part = trend_part.strip()
                      
                            if trend_part not in valid_field_value:
                                output_data_entry['errors']['trend_fields'].append(field)
                        
                elif field_value not in valid_field_value:
                    # Validate the trend value for non-current trend fields
                    output_data_entry['errors']['trend_fields'].append(field)
     
        # Check mandatory fields
        for field in mandatory_fields:
            if field not in item or not item[field]:
                output_data_entry['errors']['mandatory_fields'].append(field)

        # Validate Grade_ID
        sub_category_id = item.get("Sub_Category_ID", "")
        grade_id = item.get("Grade_ID", "")
        actual_period = item.get("Actual_Period", "")

        # Validate Sub_Category_ID, Region_ID, and Grade_ID against their respective patterns
        sub_category_valid = sub_category_pattern.match(sub_category_id)
        region_id = item.get("Region_ID", "")
        region_valid = region_pattern.match(region_id)
        grade_valid = grade_pattern.match(grade_id)

        if not sub_category_valid:
            output_data_entry['errors']['id_field_check'].append('Sub_Category_ID')
        if not region_valid:
            output_data_entry['errors']['id_field_check'].append('Region_ID')
        if not grade_id.startswith(sub_category_id + '-') or not grade_valid:
            output_data_entry['errors']['id_field_check'].append('Grade_ID')

        if sub_category_valid and region_valid and grade_valid:
            price_direct_id = f"{grade_id}_{region_id}_{actual_period}"
            item["Price_Direct_ID"] = price_direct_id

        result.append(output_data_entry)
    return result

def convert_keys_to_lowercase(input_data):   
    return [{key.lower(): value for key, value in item.items()} for item in input_data]

def actual_period_conversion(json_data):
    
    time_format = "%b-%Y%z" # month year timezone
       
    for data_entry in json_data:
        data_entry["data_ts"] = convert_time(str(time.asctime()), "%a %b %d %H:%M:%S %Y")
        data_entry["dtype"] = "price_direct"
        if data_entry["Period"] == "Monthly":
            data_entry["actual_period_str"] = data_entry["Actual_Period"]
            data_entry["Actual_Period"] = convert_time(data_entry["Actual_Period"] + "+0000", time_format)

        elif data_entry["Period"] == "Quarterly":
            time_format_quarterly = "%b %Y%z"
            quarter = data_entry["Actual_Period"][1]  # Extract the quarter digit
           
            if quarter == '1':
                data_entry["Actual_Period"] = f"Jan {data_entry['Actual_Period'][-4:]}"
            elif quarter == '2':
                data_entry["Actual_Period"] = f"Apr {data_entry['Actual_Period'][-4:]}"
            elif quarter == '3':
                data_entry["Actual_Period"] = f"Jul {data_entry['Actual_Period'][-4:]}"
            elif quarter == '4':
                data_entry["Actual_Period"] = f"Oct {data_entry['Actual_Period'][-4:]}"


            data_entry["actual_period_str"] = data_entry["Actual_Period"]
            data_entry["Actual_Period"] = convert_time(data_entry["Actual_Period"] + "+0000", time_format_quarterly)

        elif data_entry["Period"] == "Annual":
                datetime.strptime(data_entry["Actual_Period"], "%Y")
                data_entry["actual_period_str"] = data_entry["Actual_Period"]
                data_entry["Actual_Period"] = "Jan-" + data_entry["Actual_Period"]
                data_entry["Actual_Period"] = convert_time(data_entry["Actual_Period"] + "+0000", time_format)
    return json_data

def convert_time(time, time_format):    
    #obtaining given time from string
    time = datetime.strptime(time, time_format)
    #converting given time to utc timezone
    utc = tzutc()
    time_period_utc = time.astimezone(utc)
    final_time = time_period_utc.strftime("%Y-%m-%dT%H:%M:%S%z")
    return final_time


def transforming_numerical_data(input_json):    
    for data_entry in input_json:
        for field in list(data_entry.keys()):
            #print(field)
            if type(data_entry[field]) != str:
                data_entry[field] = str(data_entry[field])

            if "%" in data_entry[field]:
                data_entry[field] = data_entry[field].replace("%", "")

            if data_entry[field] == "0":
                data_entry[field] = False
            if data_entry[field] == "1":
                data_entry[field] = True    

            if field == "input_costs_percentage":
                data_entry["input_costs_percent"] = data_entry.pop(field)
            elif field == "profitability_percentage":
                data_entry["profitability_percent"] = data_entry.pop(field)
            elif field == "utilization_operating_rates_percentage":
                data_entry["utilization_operating_rates_percent"] = data_entry.pop(field)
    return input_json


def transform_supply_demand_gap(data):    
    for item in data:
        current = item.pop("supply_demand_gap_current", "")
        short_term = item.pop("supply_demand_gap_short_term", "")
        medium_term = item.pop("supply_demand_gap_medium_term", "")
        long_term = item.pop("supply_demand_gap_long_term", "")

        result = [
            {"level": "Current", "value": current},
            {"level": "Short_Term", "value": short_term},
            {"level": "Medium_Term", "value": medium_term},
            {"level": "Long_Term", "value": long_term},
        ]
        result_json = json.dumps(result)
        item["supply_demand_gap"] = result_json
    return data

def transform_supply_trend(input_data):    
    for item in input_data:
        short_term_trend = item.pop("supply_trend_short_term", "")
        long_term_trend = item.pop("supply_trend_long_term", "")
        current_trend = item.pop("supply_trend_current", "")
        medium_term_trend = item.pop("supply_trend_medium_term", "")
        
        current_trend_list = []
        for driver_trend in current_trend.split(';'):
            if driver_trend == "":
                continue
            driver, value = map(str.strip, driver_trend.split(':'))
            current_trend_list.append({"driver": driver, "value": value.lower()})

        result = [
            {"level": "Current", "trend": current_trend_list},
            {"level": "Short_Term", "value": short_term_trend.lower()},
            {"level": "Medium_Term", "value": medium_term_trend.lower()},
            {"level": "Long_Term", "value": long_term_trend.lower()},
        ]

        result_json = json.dumps(result)
        item["supply_trend"] = result_json
    return input_data

def transform_demand_trend(data):
    for item in data:
        current_trend = item.pop("demand_trend_current", "")
        short_term_trend = item.pop("demand_trend_short_term", "")
        medium_term_trend = item.pop("demand_trend_medium_term", "")
        long_term_trend = item.pop("demand_trend_long_term", "")

        current_trend_list = []
        for driver_trend in current_trend.split(';'):
            if driver_trend=="":
              continue
            driver, value = map(str.strip, driver_trend.split(':'))
            current_trend_list.append({"driver": driver, "value": value.lower()})

        current_result = {"level": "Current", "trend": current_trend_list}
        short_term_result = {"level": "Short_Term", "value": short_term_trend.lower()}
        medium_term_result = {"level": "Medium_Term", "value": medium_term_trend.lower()}
        long_term_result = {"level": "Long_Term", "value": long_term_trend.lower()}

        item["demand_trend"] = json.dumps([current_result, short_term_result, medium_term_result, long_term_result])
    return data
    

def transform_price_trend(data):
    for item in data:
        current_trend = item.pop("price_trend_current", "")
        short_term_trend = item.pop("price_trend_short_term", "")
        medium_term_trend = item.pop("price_trend_medium_term", "")
        long_term_trend = item.pop("price_trend_long_term", "")

        result = [
            {"level": "Current", "value": current_trend.lower()},
            {"level": "Short_Term", "value": short_term_trend.lower()},
            {"level": "Medium_Term", "value": medium_term_trend.lower()},
            {"level": "Long_Term", "value": long_term_trend.lower()},
        ]

        result_json = json.dumps(result)
        item["price_trend"] = result_json
    return data 

def transform_feedstock_trend(data):
    for item in data:
        current_trend = item.pop("feedstock_trend_current", "")
        short_term_trend = item.pop("feedstock_trend_short_term", "")
        medium_term_trend = item.pop("feedstock_trend_medium_term", "")
        long_term_trend = item.pop("feedstock_trend_long_term", "")

        current_trend_list = []
        for driver_trend in current_trend.split(';'):
            if driver_trend=="":
                continue
            driver, value = map(str.strip, driver_trend.split(':'))
            current_trend_list.append({"driver": driver, "value": value.lower()})

        current_result = {"level": "Current", "trend": current_trend_list}
        short_term_result = {"level": "Short_Term", "value": short_term_trend.lower()}
        medium_term_result = {"level": "Medium_Term", "value": medium_term_trend.lower()}
        long_term_result = {"level": "Long_Term", "value": long_term_trend.lower()}

        item["feedstock_trend"] = json.dumps([current_result, short_term_result, medium_term_result, long_term_result])
    return data

def transform_labor_laws(input_data):   
    for item in input_data:
        hours_of_work = item.pop("labor_laws_hours_of_work", "")
        cost_of_labor = item.pop("labor_laws_cost_of_labor", "")
        labor_supply = item.pop("labor_laws_labor_supply", "")

        result = [
            {"header": "Hours of work", "value": hours_of_work.lower()},
            {"header": "Labor Supply", "value": labor_supply.lower()},
            {"header": "Cost of Labor", "value": cost_of_labor.lower()},
        ]

        result_json = json.dumps(result)
        item["labor_laws"] = result_json
    return input_data

def transform_market_data(data):
    for item in data:
        current_commentary = item.pop("market_commentary_current", "")
        medium_term_commentary = item.pop("market_commentary_medium_term", "")
        short_term_commentary = item.pop("market_commentary_short_term", "")
        long_term_commentary = item.pop("market_commentary_long_term", "")

        market_overview = {"market_overview": current_commentary}
        market_outlook = {
            "market_outlook": f"{short_term_commentary}:{medium_term_commentary}:{long_term_commentary}"
        }

        item.update({**market_overview, **market_outlook})
    return data



def process_input_data(input_data):
    # validate data
    validate_output = validate_data(input_data)
   
    # Add errors to input_data
    for i in range(len(input_data)):
        input_data[i]['errors'] = validate_output[i]['errors']
    filtered_data = []
    error_data = []

    # Separate data into filtered and error lists
    for item in input_data:
        if any(item.get('errors', {}).get(key, False) for key in item.get('errors', {})):
            error_dict = item.pop('errors', {})
            error_dict.update(item)
            error_data.append(error_dict)
        else:
            item.pop('errors', {})
            filtered_data.append(item)

    # Process valid data
    output_actual_period_conversion    = actual_period_conversion(filtered_data)
    output_convert_keys_to_lowercase   = convert_keys_to_lowercase(output_actual_period_conversion)
    output_numerical_transform         = transforming_numerical_data(output_convert_keys_to_lowercase)
    output_transform_supply_demand_gap = transform_supply_demand_gap(output_numerical_transform)    
    output_transform_supply_trend      = transform_supply_trend(output_transform_supply_demand_gap)
    output_transform_demand_trend      = transform_demand_trend(output_transform_supply_trend)
    output_transform_price_trend       = transform_price_trend(output_transform_demand_trend)
    output_transform_feedstock_trend   = transform_feedstock_trend(output_transform_price_trend)
    output_transform_market_data       = transform_market_data(output_transform_feedstock_trend)
    output_transform_market_data       = transform_labor_laws(output_transform_market_data)

    combined_data = {"error": error_data, "processed_data": output_transform_market_data }

    return combined_data

def write_output_json(output_data, file_path):
    with open(file_path, 'w') as file:
        json.dump(output_data, file, indent=2)


def read_input_json(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' could not be found.")
        exit()
    except json.JSONDecodeError:
        print(f"Error: Unable to decode JSON from the file '{file_path}'. Please ensure it is a valid JSON file.")
        exit()
# Read the input JSON file
input_data = read_input_json('price_raw_data.json')

# Process input data
processed_data = process_input_data(input_data)

# Write the output JSON file
write_output_json(processed_data, 'output.json')