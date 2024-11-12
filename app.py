import pandas as pd
import json
import requests
from datetime import date
from bs4 import BeautifulSoup
import streamlit as st



#-------------------------------------------------------




def generatethis(year, data):

    print('Creating Evaluation for year {}...'.format(year))

    # Read the Excel file
    df = data

    # Extract the NOM_CLIENT column and remove duplicates
    unique_names = df['NOM_CLIENT'].drop_duplicates()

    # Create a new DataFrame with the unique names in the Client column
    new_df = pd.DataFrame({'Client': unique_names})

    # Add a row for "Non identifié" client
    new_df = new_df._append({'Client': 'Non identifié'}, ignore_index=True)

    # Filter duplicate for Client
    new_df.drop_duplicates(subset='Client', inplace=True)

    # Drop n/a in client
    new_df.dropna(subset=['Client'], inplace=True)

    # Write the new DataFrame to a new CSV file
    new_df.to_csv('Evolution_{}.csv'.format(year), index=False)

    # Filter the DataFrame to include non duplicated values
    df = df.drop_duplicates(subset=['NUM_CIN'])

    # Drop rows with missing values in the 'DATE_DERNIERE_CONNEXION' column
    df = df.dropna(subset=['DATE_DERNIERE_CONNEXION'])

    # Loop for each month will be stored in its own dataframe
    for month in range(1, 13):
        
        # Filter the DataFrame based on the 'DATE_DERNIERE_CONNEXION' column
        df_month = df[df['DATE_DERNIERE_CONNEXION'].apply(lambda x: pd.to_datetime(x, format='%m/%d/%Y').month) == month]
        df_month = df_month[df_month['DATE_DERNIERE_CONNEXION'].apply(lambda x: pd.to_datetime(x, format='%m/%d/%Y').year) == int(year)]

        # Filter the DataFrame to include non duplicated values
        df_month = df_month.drop_duplicates(subset=['NUM_CIN'])

        # Change the N/a in 'NOM_CLIENT' to 'Non identifié'
        df_month['NOM_CLIENT'] = df_month['NOM_CLIENT'].fillna('Non identifié')

        # Count the occurrences of each NOM_CLIENT
        count = df_month['NOM_CLIENT'].value_counts()

        # If 'Non identifié' exists
        if 'Non identifié' in count:
            # Move 'Non identifié' to the last row
            count = count.reindex(count.index.drop('Non identifié').tolist() + ['Non identifié'])


        # Get the name of the month in French
        month_name = pd.to_datetime(str(month), format='%m').strftime('%B')

        # Read the output CSV file into a DataFrame
        output_df = pd.read_csv('Evolution_{}.csv'.format(year))

        # Merge the count DataFrame with the output DataFrame based on the 'NOM_CLIENT' column
        merged_df = pd.merge(output_df, count, how='left', left_on='Client', right_index=True)

        # Fill missing values with 0
        merged_df.fillna(0, inplace=True)

        # Rename the count column to the name of the month
        merged_df.rename(columns={'count': month_name}, inplace=True)

        # Convert the count column to string and remove decimal places
        merged_df[month_name] = merged_df[month_name].astype(int).astype(str)

        # Save the merged DataFrame to a CSV file
        merged_df.to_csv('Evolution_{}.csv'.format(year), index=False)

    # Read the output CSV file into a DataFrame
    output_df = pd.read_csv('Evolution_{}.csv'.format(year))

    # Calculate the sum of the months for each row
    output_df['Total'] = output_df.iloc[:, 1:].sum(axis=1)

    # Save the modified DataFrame to a new CSV file
    output_df.to_csv('Evolution_{}.csv'.format(year), index=False)




#-------------------------------------------------------


def generate(year, data):

    print('Creating Global Evaluation...')

    # Read the Excel file
    df = data

    # Backup the DataFrame
    bdf = df

    for y in range(2020, int(year)+1):

        #   Reset the df
        df = bdf

        # Filter the DataFrame to include non duplicated values
        df = df.drop_duplicates(subset=['NUM_CIN'])

        # Drop rows with missing values in the 'DATE_DERNIERE_CONNEXION' column
        df = df.dropna(subset=['DATE_DERNIERE_CONNEXION'])
        
        # Filter the DataFrame based on the year
        df = df[df['DATE_DERNIERE_CONNEXION'].apply(lambda x: pd.to_datetime(x, format='%m/%d/%Y').year) == int(y)]

        # Change the N/a in 'NOM_CLIENT' to 'Non identifié'
        df['NOM_CLIENT'] = df['NOM_CLIENT'].fillna('Non identifié')

        # Count the occurrences of each NOM_CLIENT
        count = df['NOM_CLIENT'].value_counts()

        # If 'Non identifié' exists
        if 'Non identifié' in count:
            # move 'Non identifié' to the last row
            count = count.reindex(count.index.drop('Non identifié').tolist() + ['Non identifié'])

        # Save the count for each NOM_CLIENT to a CSV file
        count.to_csv('cache/output_{}.csv'.format(str(y)))


#-------------------------------------------------------


def group(year):

    print('Grouping data for year {}...'.format(year))
    # Initialize an empty DataFrame to hold the merged data
    merged_df = pd.DataFrame()

    # Loop through each year's CSV file
    for y in range(2020, int(year) + 1):
        # Read the CSV file for the current year
        df = pd.read_csv('cache/output_{}.csv'.format(y))
        
        # Rename the count column to the year
        df.rename(columns={'NOM_CLIENT': 'Client', 'count': str(y)}, inplace=True)
        
        # Convert the count column to integers
        df[str(y)] = df[str(y)].fillna(0).astype(int)

        # Merge the current year's data with the merged DataFrame
        if merged_df.empty:
            merged_df = df
        else:
            merged_df = pd.merge(merged_df, df, on='Client', how='outer')
        
    

    # Fill missing values with 0
    merged_df.fillna(0, inplace=True)

    # Calculate the sum of the months for each row
    merged_df['Total'] = merged_df.iloc[:, 1:].sum(axis=1)

    # remove .0 from the all columns
    for col in ['Total', '2020', '2021', '2022', '2023', '2024']:
        merged_df[col] = merged_df[col].astype(int).astype(str)

    # Save the merged DataFrame to a new CSV file
    merged_df.to_csv('Evolution_Global.csv', index=False)


#-------------------------------------------------------


# Play Store Scraping
def scrape_play(app_name):
    url = f"https://www.google.com/search?q={app_name} play store"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    data = soup.text
    return data

#App Store Scraping
def scrape_apple(app_name):
    url = f"https://www.google.com/search?q={app_name} apple store"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    data = soup.text
    return data

# LLM API
def send_to_ai_api(prompt):
    api_url = "https://a.picoapps.xyz/ask-ai"
    response = requests.get(api_url, params={'prompt': prompt})
    return response.json()['response']


#-------------------------------------------------------    


def generate_taux_util(year,month,data):


    
    # Read the Excel file
    df = data

    print('Operating for utilisation rate...')

    # Filter the DataFrame to include non duplicated values
    df = df.drop_duplicates(subset=['NUM_CIN'])


    # Change the N/a in 'NOM_CLIENT' to 'Non identifié'
    df['NOM_CLIENT'] = df['NOM_CLIENT'].fillna('Non identifié')


    # Drop rows with missing values in the 'DATE_DERNIERE_UTILISATION' column
    df = df.dropna(subset=['DATE_DERNIERE_UTILISATION'])
        
    # Count the occurrences of each NOM_CLIENT
    count = df['NOM_CLIENT'].value_counts()

    # If 'Non identifié' exists
    if 'Non identifié' in count:
            # move 'Non identifié' to the last row
        count = count.reindex(count.index.drop('Non identifié').tolist() + ['Non identifié'])


    # Filter the DataFrame based on the specified year and month
    df = df[df['DATE_DERNIERE_UTILISATION'].apply(lambda x: pd.to_datetime(x, format='%m/%d/%Y').month) == month]
    df = df[df['DATE_DERNIERE_UTILISATION'].apply(lambda x: pd.to_datetime(x, format='%m/%d/%Y').year) == int(year)]

    # count new occurences of NOM_CLIENT
    count2 = df['NOM_CLIENT'].value_counts()

    # If 'Non identifié' exists
    if 'Non identifié' in count2:
            # move 'Non identifié' to the last row
        count2 = count2.reindex(count2.index.drop('Non identifié').tolist() + ['Non identifié'])

    # merge the new occurences with the old ones in one df, each in a column with client as index
    countf = pd.concat([count, count2], axis=1)

    #fill missing values with 0
    countf.fillna(0, inplace=True)

    #rename the columns
    countf.columns = ['Total_users', 'utilisateur_actuel']

    #calculate the taux d'utilisation
    countf['taux_utilisation'] = countf['utilisateur_actuel'] / countf['Total_users']

    #no floats in new column
    countf['Total_users'] = countf['Total_users'].astype(str)
    countf['utilisateur_actuel'] = countf['utilisateur_actuel'].astype(int).astype(str)

    #calculate the percentage of taux d'utilisation
    countf['taux_utilisation'] = countf['taux_utilisation'] * 100 

    #round the percentage to 2 decimal places
    countf['taux_utilisation'] = countf['taux_utilisation'].round(2)

    #convert the percentage to string
    countf['taux_utilisation'] = countf['taux_utilisation'].astype(str) + '%'


    #save the merged dataframe to a csv file
    countf.to_csv('taux_utilisation.csv')
    

#-------------------------------------------------------


def generate_taux_tele(data,all):


    
    # Read the Excel file
    df = data
    df2 = all

    print('Operating for download rate...')

    # Filter the DataFrame to include non duplicated values
    df = df.drop_duplicates(subset=['NUM_CIN'])
    df2 = df2.drop_duplicates(subset=['NUM_CIN'])


    # Change the N/a in 'NOM_CLIENT' to 'Non identifié'
    df['NOM_CLIENT'] = df['NOM_CLIENT'].fillna('Non identifié')
    df2['NOM_CLIENT'] = df2['NOM_CLIENT'].fillna('Non identifié')

        
    # Count the occurrences of each NOM_CLIENT
    count = df['NOM_CLIENT'].value_counts()
    count2 = df2['NOM_CLIENT'].value_counts()

    # If 'Non identifié' exists
    if 'Non identifié' in count:
            # move 'Non identifié' to the last row
        count = count.reindex(count.index.drop('Non identifié').tolist() + ['Non identifié'])
    
    if 'Non identifié' in count2:
            # move 'Non identifié' to the last row
        count2 = count2.reindex(count2.index.drop('Non identifié').tolist() + ['Non identifié'])



    # merge the new occurences with the old ones in one df, each in a column with client as index
    countf = pd.concat([count, count2], axis=1)

    #fill missing values with 0
    countf.fillna(0, inplace=True)

    #rename the columns
    countf.columns = ['Total_users', 'Total_adherents']

    #calculate the taux de telechargement
    countf['taux_telechargement'] = countf['Total_users'] / countf['Total_adherents']

    #no floats in new column
    countf['Total_users'] = countf['Total_users'].astype(str)
    countf['Total_adherents'] = countf['Total_adherents'].astype(str)

    #calculate the percentage of taux de telechargement
    countf['taux_telechargement'] = countf['taux_telechargement'] * 100 

    #round the percentage to 2 decimal places
    countf['taux_telechargement'] = countf['taux_telechargement'].round(2)

    #convert the percentage to string
    countf['taux_telechargement'] = countf['taux_telechargement'].astype(str) + '%'


    #save the merged dataframe to a csv file
    countf.to_csv('taux_telechargement.csv')
    

#-------------------------------------------------------


def generate_ratings():
    # CSV
    df = pd.read_csv("apps.csv")

    print("Processing Stores Rating Data...")

    # Loop on DataFrame
    for index, row in df.iterrows():
            while True:
                try:
                    if row["Nom de l'application"] == "Indispo sur les stores":
                        break
                    # Scraping raw data...
                    scraped_data_play = scrape_play(row["Nom de l'application"])
                    # print("--------------------")
                    # print(scraped_data_play)
                    # print("--------------------")
                    scraped_data_App = scrape_apple(row["Nom de l'application"])
                    # print(scraped_data_App)
                    #print("--------------------")
                    #print(row["Nom de l'application"])
                    
                    # Prompt
                    prompt = f'''Please classify the following information and return for me a json that contain : Note de l'app au playstore et nombre total des avis de playstore et Note de l'app dans apple store et nombre total des avis dans apple store'); the format for notes are 0.0 and on 5 , don't use / in notes ; Extracted Data from playstore: {scraped_data_play} and Extracted Data from apptore : {scraped_data_App} ; Remember to use this format: {{ 'note-playstore': x,'avis-playstore': x, 'note-applestore': x,'avis-applestore': x}} you should always use and respect this format, only generate the json with the data requested, don't add any other information; '''
                    
                    # AI API call
                    ai_response = send_to_ai_api(prompt)
                    
                    #print(ai_response)

                    ai_response = json.loads(ai_response)

                    note_playstore = str(ai_response['note-playstore'])
                    df.at[index, "note-playstore"] = note_playstore

                    avis_playstore = str(ai_response['avis-playstore'])
                    df.at[index, "avis-playstore"] = avis_playstore

                    note_applestore = str(ai_response['note-applestore'])
                    df.at[index, "note-applestore"] = note_applestore

                    avis_applestore = str(ai_response['avis-applestore'])
                    df.at[index, "avis-applestore"] = avis_applestore

                    break  
                except Exception as e:
                    print(f"An error occurred. Retrying...")

    # Save the DataFrame to a new CSV file
    df.to_csv("Rating_Stores.csv", index=False)


#-------------------------------------------------------



def save_all():

    # Get the current year
    year = date.today().strftime("%Y")

    # List of CSV files
    csv_files = [
        'Evolution_{}.csv'.format(year),
        'Evolution_Global.csv',
        'taux_telechargement.csv',
        'taux_utilisation.csv',
        'Rating_Stores.csv'
    ]

    # Create a Pandas Excel writer using XlsxWriter as the engine
    with pd.ExcelWriter('Rapport_Appli_Mobile.xlsx', engine='xlsxwriter') as writer:
        for csv_file in csv_files:
            # Read each CSV file
            df = pd.read_csv(csv_file)
            # Use the file name (without extension) as the sheet name
            sheet_name = csv_file.split('.')[0]
            # Write the dataframe to the specified sheet
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print("Excel file created successfully.")



# -------------------------------------------------------

def main():

     # Apply custom CSS to change button color to green
    st.markdown("""
        <style>
        .stButton button {
            margin-top: 3rem !important;
            background-color: #00a631 !important;
            border-color: #00a631 !important;
            color: white !important;
        }

        .stButton button:hover {
            background-color: green !important;
            border-color: green !important;
            color: white !important;
        }
            

        </style>
        """, unsafe_allow_html=True)
    
    print('Running the script...')

    # Streamlit interface
    st.title("🗎 AFMA : Generateur de Rapport d'Application Mobile format Excel ")

    # File uploader
    uploaded_file = st.file_uploader("Veuillez télécharger le fichier Excel que vous souhaitez utiliser", type=["xlsx", "xls", "xltx", "xlsm", "xltm", "xlam", "xlsb", "csv", "txt"])

    # Month selector
    month = st.selectbox("Veuillez sélectionner le mois de fin de la collecte des données", [f"{i:02d}" for i in range(1, 13)])

    # Get the current year
    year = date.today().strftime("%Y")

   

    # create button to process the data
    if st.button("Generate!", key="generate_button", help="Click to process the data", use_container_width=True, type="primary") and uploaded_file is not None:

        # Display a message
        st.info("Processing the data...")

        # mask the generate button
        st.markdown("""
            <style>
            .stButton button {
                display: none !important;
            }
            </style>
            """, unsafe_allow_html=True)

        print('Processing the file...')

         # Read the uploaded Excel file if it is excel and read csv if it is txt or csv
        if uploaded_file.name.endswith('.xlsx') or uploaded_file.name.endswith('.xls') or uploaded_file.name.endswith('.xltx') or uploaded_file.name.endswith('.xlsm') or uploaded_file.name.endswith('.xltm') or uploaded_file.name.endswith('.xlam') or uploaded_file.name.endswith('.xlsb'):
            data = pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith('.csv') or uploaded_file.name.endswith('.txt'):
            data = pd.read_csv(uploaded_file)

        print('Processing the data...')

        # Process the data
        generatethis(year, data)
        generate(year, data)
        group(year)
        generate_taux_util(year, month, data)
        generate_taux_tele(data, data)
        generate_ratings()
        save_all()

        st.success("Processing complete.")

        # mask the generate button
        st.markdown("""
            <style>
            .stButton button {
                display: block !important;
            }
            </style>
            """, unsafe_allow_html=True)


        # download Rapport_Appli_Mobile.xlsx
        st.markdown("### Download the Excel file")

        with open("Rapport_Appli_Mobile.xlsx", "rb") as file:
            btn = st.download_button(
                label="Download Rapport_Appli_Mobile.xlsx 📁",
                data=file,
                file_name="Rapport_Appli_Mobile.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_button"
            )


if __name__ == "__main__":
    main()


#-------------------------------------------------------

