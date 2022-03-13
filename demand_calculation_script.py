import pandas as pd
import numpy as np
import sqlite3

# Import CSV files as DataFrames
calls_for_food = pd.read_csv('BC211_CallsForFood2021.csv')
population_demographics = pd.read_csv('Population_demographics_summary.csv')

# Filter cities and total population from demographis DF
population_demographics_cities_total = population_demographics.filter(items=['Census SubDivision Name','Total Population'])

# Filter numbers of Age 60+ people from DF
population_demographics_old = population_demographics.filter(regex=r'(Total Pop Age 6|Total Pop Age 7|Total Pop Age 8)',axis=1)

# Get sum of Age 60+ people in each demographic area
population_demographics_old['Total Old'] = population_demographics_old.sum(axis=1)
population_demographics_old = population_demographics_old['Total Old']

# Concatenate 60+ DF onto city/total population DF
population_demographics_filtered = pd.concat([population_demographics_cities_total,population_demographics_old],axis=1)

# Initialize total population and total old population columns on 211 calls DF
calls_for_food['Total Pop']=0
calls_for_food['Total Old']=0

# Update 'Total Pop' and 'Total Old' columns with values from demographics DF
for i in range(calls_for_food.shape[0]):
    city = str(calls_for_food.at[i,'City'])
    for j in range(population_demographics_filtered.shape[0]):
        if str(population_demographics_filtered.at[j,'Census SubDivision Name']).startswith(city):
            calls_for_food.at[i,'Total Pop'] = population_demographics_filtered.at[j,'Total Population']
            calls_for_food.at[i,'Total Old'] = population_demographics_filtered.at[j,'Total Old']

# Create age factor for each city (otal population / total 60+ people)
calls_for_food['age_factor'] = calls_for_food['Total Pop'] / calls_for_food['Total Old']

# Replace infinity values with null
calls_for_food.replace([np.inf, -np.inf], np.nan, inplace=True)

# Get adjusted number of hungry people
calls_for_food['adjusted_hungry_people'] = calls_for_food['Total'] * calls_for_food['age_factor']

# Filter down to just city and adjusted hungry people call number
calls_for_food_age_adjusted = calls_for_food.filter(items=['City','adjusted_hungry_people'])

# Get average age factor for dealing with null values
avg_factor = calls_for_food['age_factor'].mean(skipna=True)

# Replace null values with 0
calls_for_food_age_adjusted.replace(np.nan, 0, inplace=True)

# Update 0 values with the original total calls times the average age adjustment factor
for i in range(calls_for_food_age_adjusted.shape[0]):
    if calls_for_food_age_adjusted.at[i,'adjusted_hungry_people'] == 0:
        calls_for_food_age_adjusted.at[i,'adjusted_hungry_people'] = calls_for_food.at[i,'Total'] * avg_factor

# Round the adjusted call number
calls_for_food_age_adjusted['adjusted_hungry_people'] = calls_for_food_age_adjusted['adjusted_hungry_people'].round()

# Save new data as CSV
calls_for_food_age_adjusted.to_csv('cleaned_number_of_calls.csv')

# Create new SQLite connection
conn = sqlite3.connect('adjusted_calls.sqlite')

# Insert calls DF as table
calls_for_food_age_adjusted.to_sql(name='city_calls',con=conn,if_exists='replace',index_label='city_id')

# Initialize cursor to send commands
cursor = conn.cursor()

# Check that table was correctly inserted
cursor.execute('SELECT * FROM city_calls')

# Fetch and print rows
rows = cursor.fetchall()

for row in rows:
    print(row)

# Close connection
conn.close()