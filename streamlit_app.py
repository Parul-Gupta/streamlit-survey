import streamlit as st
import pandas as pd
import os, json

import streamlit_survey as ss
from streamlit_gsheets import GSheetsConnection

# -----------------------------------------------------------------------------
# Declare some useful functions.

def get_characteristics_options(char):
    characteristic_options_dict = {
        "Photography Genre": ["Architectural", "Candid", "Staged", "Portrait", "Selfie", "Group", "Product", "Fashion", "Beauty", "Bridal", "Interior", "Street", "Landscape", "Sky", "Still-life", "Action", "Underwater", "Botanical", "Historical", "Amateur", "Abstract", "Live stage"],
        "Clothing Style": ["Casual", "Athletic", "Formal", "Business", "Swimwear", "Business casual", "Traditional", "Protective", "Beachwear", "Costume", "Form fitting"],
        "Gaze": ["Forward", "Downward", "Sideways", "Away", "Upward", "Outward", "Engaged"],
        "Posing": ["Standing", "Seated", "Holding", "Leaning", "Active", "Reclined", "Walking", "Stretching", "Dynamic", "Running", "Relaxed", "Confident"],
        "Hair Style": ["Short", "Covered", "Wavy", "Loose", "Varied", "Straight", "Neat", "Ponytail", "Casual", "Tied back", "Flowing", "Curly", "Updo", "Pulled back", "Braided"],
        "Image Lighting": ["Bright", "Dark", "Moderate", "Studio", "Natural", "Soft", "Hard", "Light glare", "Vignette", "Colored", "Light on subject"],
        "Depth": ["Wide angle shot", "Mid shot", "Close up shot", "Macro shot", "Motion blur", "Radial blur", "Gaussian blur", "Fully focused subject", "Unfocused subject", "Partly focused subject", "Bokeh effect", "Isolated focal point", "Multiple focal points", "Bright focal point", "Dark focal point", "Shallow depth of field"],
        "Visible Body Section": ["Upper body", "Full body", "Hand only", "Lower half", "Close up", "Midsection", "Full back", "Head shot"],
        "Perspective": ["Bird eye view", "Worm eye view", "Fish eye view", "Panorama view", "Centered composition", "Rule of third", "Altered perspective", "Framed image", "High angle photo", "Low angle photo", "Vertical composition", "Corner shot", "Point of view shot", "Audience perspective"]
    }
    return characteristic_options_dict[char]

def get_spreadsheet_data_online():
    import gspread
    from gspread_dataframe import get_as_dataframe
    from oauth2client.service_account import ServiceAccountCredentials
    from google.oauth2.service_account import Credentials
    import requests

    im_url = "https://www.googleapis.com/drive/v3/files/{0}?alt=media"

    # Authenticate and access Google Sheet
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('creds/streamlit-survey-448423.json', scope)
    credentials = Credentials.from_service_account_file(
        'creds/streamlit-survey-448423.json',
        scopes=scope
    )
    client = gspread.authorize(creds)
    gc = gspread.authorize(credentials)
    # print(client.list_spreadsheet_files())
    google_sheet = client.open('Streamlit Survey Sheet')

    output_sheet = google_sheet.worksheet("Output Sheet")
    input_sheet = google_sheet.worksheet("Input Sheet")
    questions_df = get_as_dataframe(input_sheet)

    return questions_df, output_sheet

def get_spreadsheet_data_local():
    questions_df = pd.read_excel(os.path.join("data", "excel", "Streamlit Survey Sheet.xlsx"), sheet_name="Input Sheet")
    return questions_df

def process_local_questions_data(questions_df):
    brand1_names = questions_df["Brand1"].to_list()
    brand_im1_ids = questions_df["Brand1ImPath"].to_list()
    # responses1 = [requests.get(im_url.format(img_id), headers={'Authorization': f'Bearer {credentials.token}'})  for img_id in brand_im1_ids]
    # print(resp.status_code for resp in responses1)
    # brand_im1_images = [BytesIO(resp.content) for resp in responses1]

    brand2_names = questions_df["Brand2"].to_list()
    brand_im1_images = [os.path.join("data", "images", img_id) for img_id in brand_im1_ids]

    # print(type(brand_im1_images[0]))

    brand_im2_ids = questions_df["Brand2ImPath"].to_list()
    # responses2 = [requests.get(im_url.format(img_id), headers={'Authorization': f'Bearer {credentials.token}'})  for img_id in brand_im2_ids]
    # print(resp.status_code for resp in responses2)
    # brand_im2_images = [BytesIO(resp.content) for resp in responses2]

    brand_im2_images = [os.path.join("data", "images", img_id) for img_id in brand_im2_ids]

    brand_options = questions_df["Options"].to_list()
    brand_options = [eval(i) for i in brand_options]
    return brand1_names, brand2_names, brand_im1_images, brand_im2_images, brand_options

def store_state_on_submit(survey1):
    survey_json = json.loads(survey1.to_json())

    diction = {k:survey_json[k]["value"] for k in survey_json}

    # can't do this because the storage is not persistent across sessions
    # output_sheet_df = pd.read_excel(os.path.join("data", "excel", "Streamlit Survey Sheet.xlsx"), sheet_name="Output Sheet")

    conn = st.connection("gsheets", type=GSheetsConnection)
    output_sheet_df = conn.read(worksheet="Output Sheet")
    output_sheet_df = pd.concat([output_sheet_df, pd.DataFrame([diction])], ignore_index=True)

    # with pd.ExcelWriter(os.path.join("data", "excel", "Streamlit Survey Sheet.xlsx"), engine='openpyxl', if_sheet_exists="overlay", mode="a") as writer:
    #     output_sheet_df.to_excel(excel_writer=writer, sheet_name="Output Sheet", index=None)

    conn.update(worksheet="Output Sheet", data=output_sheet_df)
    st.cache_data.clear()
    st.session_state["submitted"] = True
    st.rerun()
    return

def get_submit_button(label="Submit"):
    return lambda pages: st.button(
        label=label,
        use_container_width=True,
        key=f"{pages.current_page_key}_btn_next",
        disabled=st.session_state["submitted"] or not st.session_state["selected_chars"] or not st.session_state["char1_different"] or not st.session_state["char2_different"]
    )

def get_previous_button(label="Previous"):
    return lambda pages: st.button(
        label,
        use_container_width=True,
        on_click=pages.previous,
        disabled=pages.current == 0 or st.session_state["submitted"],
        key=f"{pages.current_page_key}_btn_prev",
    )

def get_next_button(label="Next"):
    return lambda pages: st.button(
        label,
        use_container_width=True,
        on_click=pages.next,
        disabled=(pages.current == pages.n_pages - 1) or (pages.current == 0 and not st.session_state["agree_value"]) or (pages.current > 1 and (not st.session_state["selected_chars"] or not st.session_state["char1_different"] or not st.session_state["char2_different"]) ),
        key=f"{pages.current_page_key}_btn_next",
    )

# @st.cache_data
# def get_gdp_data():
#     """Grab GDP data from a CSV file.

#     This uses caching to avoid having to read the file every time. If we were
#     reading from an HTTP endpoint instead of a file, it's a good idea to set
#     a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
#     """

#     # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
#     DATA_FILENAME = Path(__file__).parent/'data/gdp_data.csv'
#     raw_gdp_df = pd.read_csv(DATA_FILENAME)

#     MIN_YEAR = 1960
#     MAX_YEAR = 2022

#     # The data above has columns like:
#     # - Country Name
#     # - Country Code
#     # - [Stuff I don't care about]
#     # - GDP for 1960
#     # - GDP for 1961
#     # - GDP for 1962
#     # - ...
#     # - GDP for 2022
#     #
#     # ...but I want this instead:
#     # - Country Name
#     # - Country Code
#     # - Year
#     # - GDP
#     #
#     # So let's pivot all those year-columns into two: Year and GDP
#     gdp_df = raw_gdp_df.melt(
#         ['Country Code'],
#         [str(x) for x in range(MIN_YEAR, MAX_YEAR + 1)],
#         'Year',
#         'GDP',
#     )

#     # Convert years from string to integers
#     gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])

#     return gdp_df

# gdp_df = get_gdp_data()

questions_df = get_spreadsheet_data_local()
brand1_names, brand2_names, brand_im1_images, brand_im2_images, brand_options = process_local_questions_data(questions_df)

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='BrandFusion User Survey',
    page_icon=':earth_americas:', # This is an emoji shortcode. Could be a URL too.
)
survey = ss.StreamlitSurvey("User Survey")

# to be used to empty the survey form upon submitting
empty_placeholder = st.empty()
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False

# Set the title that appears at the top of the page.
First_Title = '''
# :earth_americas: BrandFusion: Aligning Image Generation with Brand Styles (User Survey)

Explanatory Statement\n
Aim: This work aims to introduce brand identity in the automatic generation of promotional media. Therefore we establish a set of characteristics that constitute the visual identity of each brand. The aim of this user study is to measure the degree of correspondence between the brand identity defined by us and human perception.\n
Duration: This study has a total of 60 questions, each needing 1-1.5 minutes to respond. (Total time needed is 60-90 minutes.)\n
Eligibility: The participant must be above 18 years of age.\n
Data Collection and Storage: The survey is anonymous, and only your responses to the questions will be recorded. The survey responses will be stored for a period of 5 years on Monash Data Servers and will only be accessible for research purposes.\n
Contact Details: For further details about the research and how your responses will be used, please contact any of the following people:\n
1. Parul (parul@monash.edu)\n
2. Abhinav Dhall (abhinav.dhall@monash.edu)\n
3. Varun Khurana\n
4. Yaman Kumar\n
'''

# Add some spacing
''
''

Agree_Box = ss.CheckBox(survey=survey, label="I fit the eligibility criteria and agree to participate in the survey.", id="Agree_box", value=True)
Second_Title = '''
In each of the following questions, you'll be shown two sets of (advertisement) images from two different brands of the same sector (e.g. 2 Fashion brands, 2 Airlines brands etc.). Then, from a given list of characteristics, you'll need to choose which are the most differentiating characteristics between the two sets of images. Also, you'll need to assign the labels per characteristic which are relevant to each set of images.\n
'''

Question_template = '''
Choose 2 most distinctive characteristics between the below sets of images.
'''
Question_components = [ss.MultiSelect(survey=survey, label="Select in order of distinctiveness (most distinctive first):", id=f"Characteristic_component_{itr}", key=f"Characteristic_component_{itr}", options=brand_options[itr]) for itr in range(questions_df.shape[0])]

FollowUp_Question_template = '''
{0} in {1} images'''
# st.session_state["Brand1_FollowUp_Char1_Options"] = [["default"] for _ in range(questions_df.shape[0])]
# st.session_state["Brand2_FollowUp_Char1_Options"] = [["default"] for _ in range(questions_df.shape[0])]
# st.session_state["Brand1_FollowUp_Char2_Options"] = [["default"] for _ in range(questions_df.shape[0])]
# st.session_state["Brand2_FollowUp_Char2_Options"] = [["default"] for _ in range(questions_df.shape[0])]
Brand1_FollowUp_Char1_components = [None for itr in range(questions_df.shape[0])]

Brand2_FollowUp_Char1_components = [None for itr in range(questions_df.shape[0])]

Brand1_FollowUp_Char2_components = [None for itr in range(questions_df.shape[0])]

Brand2_FollowUp_Char2_components = [None for itr in range(questions_df.shape[0])]
    
pages = survey.pages(questions_df.shape[0]+2, progress_bar=True, on_submit=lambda: store_state_on_submit(survey1=survey))

pages.submit_button = get_submit_button()
pages.prev_button = get_previous_button()
pages.next_button = get_next_button()

with pages:
    if pages.current == 0:
        st.write(First_Title)
        agree_value = Agree_Box.display()
        if not agree_value:
            st.session_state["agree_value"] = False
            st.error("Please agree to the terms and conditions before proceeding")
        else:
            st.session_state["agree_value"] = True
    elif pages.current == 1:
        st.write(Second_Title)
    else:
        if pages.current == pages.n_pages-1:
            with empty_placeholder.container():
                # use empty placeholder only for last page
                st.write(Question_template)
                st.image(brand_im1_images[pages.current-2], caption=f"{brand1_names[pages.current-2]}")
                st.image(brand_im2_images[pages.current-2], caption=f"{brand2_names[pages.current-2]}")
                characteristic_value = Question_components[pages.current-2].display()
                if len(characteristic_value) != 2:
                    st.session_state["selected_chars"] = False
                    st.error(f"Please select 2 options.")
                else:
                    st.session_state["selected_chars"] = True
                    # st.session_state["Brand1_FollowUp_Char1_Options"][pages.current-2] = get_characteristics_options(characteristic_value[0])
                    # st.session_state["Brand1_FollowUp_Char2_Options"][pages.current-2] = get_characteristics_options(characteristic_value[1])
                    # st.session_state["Brand2_FollowUp_Char1_Options"][pages.current-2] = get_characteristics_options(characteristic_value[0])
                    # st.session_state["Brand2_FollowUp_Char2_Options"][pages.current-2] = get_characteristics_options(characteristic_value[1])

                    Brand1_FollowUp_Char1_components[pages.current-2] = ss.SelectBox(survey=survey, label=f"Brand1_FollowUp_Char1_component_{pages.current-2}", label_visibility="collapsed", options=get_characteristics_options(characteristic_value[0]), key=f"Brand1_FollowUp_Char1_component_{pages.current-2}")

                    Brand2_FollowUp_Char1_components[pages.current-2] = ss.SelectBox(survey=survey, label=f"Brand2_FollowUp_Char1_component_{pages.current-2}", label_visibility="collapsed", options=get_characteristics_options(characteristic_value[0]), key=f"Brand2_FollowUp_Char1_component_{pages.current-2}")

                    Brand1_FollowUp_Char2_components[pages.current-2] = ss.SelectBox(survey=survey, label=f"Brand1_FollowUp_Char2_component_{pages.current-2}", label_visibility="collapsed", options=get_characteristics_options(characteristic_value[1]), key=f"Brand1_FollowUp_Char2_component_{pages.current-2}")

                    Brand2_FollowUp_Char2_components[pages.current-2] = ss.SelectBox(survey=survey, label=f"Brand2_FollowUp_Char2_component_{pages.current-2}", label_visibility="collapsed", options=get_characteristics_options(characteristic_value[1]), key=f"Brand2_FollowUp_Char2_component_{pages.current-2}")

                    st.write(FollowUp_Question_template.format(characteristic_value[0], brand1_names[pages.current-2]))
                    brand1_char1_value = Brand1_FollowUp_Char1_components[pages.current-2].display()

                    st.write(FollowUp_Question_template.format(characteristic_value[0], brand2_names[pages.current-2]))
                    brand2_char1_value = Brand2_FollowUp_Char1_components[pages.current-2].display()

                    if brand1_char1_value == brand2_char1_value:
                        st.session_state["char1_different"] = False
                        st.error(f"The {characteristic_value[0]} for both the brands should be different!")
                    else:
                        st.session_state["char1_different"] = True

                    st.write(FollowUp_Question_template.format(characteristic_value[1], brand1_names[pages.current-2]))
                    brand1_char2_value = Brand1_FollowUp_Char2_components[pages.current-2].display()

                    st.write(FollowUp_Question_template.format(characteristic_value[1], brand2_names[pages.current-2]))
                    brand2_char2_value = Brand2_FollowUp_Char2_components[pages.current-2].display()

                    if brand1_char2_value == brand2_char2_value:
                        st.session_state["char2_different"] = False
                        st.error(f"The {characteristic_value[1]} for both the brands should be different!")
                    else:
                        st.session_state["char2_different"] = True
            
            if st.session_state["submitted"] == True:
                empty_placeholder.empty()
                st.success("Survey submitted successfully!")
        else:
            # don't use empty placeholder for other pages
            st.write(Question_template)
            st.image(brand_im1_images[pages.current-2], caption=f"{brand1_names[pages.current-2]}")
            st.image(brand_im2_images[pages.current-2], caption=f"{brand2_names[pages.current-2]}")
            characteristic_value = Question_components[pages.current-2].display()
            if len(characteristic_value) != 2:
                st.session_state["selected_chars"] = False
                st.error(f"Please select 2 options.")
            else:
                st.session_state["selected_chars"] = True
                # st.session_state["Brand1_FollowUp_Char1_Options"][pages.current-2] = get_characteristics_options(characteristic_value[0])
                # st.session_state["Brand1_FollowUp_Char2_Options"][pages.current-2] = get_characteristics_options(characteristic_value[1])
                # st.session_state["Brand2_FollowUp_Char1_Options"][pages.current-2] = get_characteristics_options(characteristic_value[0])
                # st.session_state["Brand2_FollowUp_Char2_Options"][pages.current-2] = get_characteristics_options(characteristic_value[1])

                Brand1_FollowUp_Char1_components[pages.current-2] = ss.SelectBox(survey=survey, label=f"Brand1_FollowUp_Char1_component_{pages.current-2}", label_visibility="collapsed", options=get_characteristics_options(characteristic_value[0]), key=f"Brand1_FollowUp_Char1_component_{pages.current-2}")

                Brand2_FollowUp_Char1_components[pages.current-2] = ss.SelectBox(survey=survey, label=f"Brand2_FollowUp_Char1_component_{pages.current-2}", label_visibility="collapsed", options=get_characteristics_options(characteristic_value[0]), key=f"Brand2_FollowUp_Char1_component_{pages.current-2}")

                Brand1_FollowUp_Char2_components[pages.current-2] = ss.SelectBox(survey=survey, label=f"Brand1_FollowUp_Char2_component_{pages.current-2}", label_visibility="collapsed", options=get_characteristics_options(characteristic_value[1]), key=f"Brand1_FollowUp_Char2_component_{pages.current-2}")

                Brand2_FollowUp_Char2_components[pages.current-2] = ss.SelectBox(survey=survey, label=f"Brand2_FollowUp_Char2_component_{pages.current-2}", label_visibility="collapsed", options=get_characteristics_options(characteristic_value[1]), key=f"Brand2_FollowUp_Char2_component_{pages.current-2}")

                st.write(FollowUp_Question_template.format(characteristic_value[0], brand1_names[pages.current-2]))
                brand1_char1_value = Brand1_FollowUp_Char1_components[pages.current-2].display()

                st.write(FollowUp_Question_template.format(characteristic_value[0], brand2_names[pages.current-2]))
                brand2_char1_value = Brand2_FollowUp_Char1_components[pages.current-2].display()

                if brand1_char1_value == brand2_char1_value:
                    st.session_state["char1_different"] = False
                    st.error(f"The {characteristic_value[0]} for both the brands should be different!")
                else:
                    st.session_state["char1_different"] = True

                st.write(FollowUp_Question_template.format(characteristic_value[1], brand1_names[pages.current-2]))
                brand1_char2_value = Brand1_FollowUp_Char2_components[pages.current-2].display()

                st.write(FollowUp_Question_template.format(characteristic_value[1], brand2_names[pages.current-2]))
                brand2_char2_value = Brand2_FollowUp_Char2_components[pages.current-2].display()

                if brand1_char2_value == brand2_char2_value:
                    st.session_state["char2_different"] = False
                    st.error(f"The {characteristic_value[1]} for both the brands should be different!")
                else:
                    st.session_state["char2_different"] = True
            
            

# Create Streamlit survey form
# st.title("User Survey")
# name = st.text_input("What is your name?")
# age = st.number_input("What is your age?", min_value=0, max_value=120)
# feedback = st.text_area("Any feedback?")

# if st.button("Submit Survey"):
#     # Save data to Google Sheet
#     output_sheet.append_row([name, age, feedback])
#     st.success("Survey submitted successfully!")

# if st.button("View Results"):
#     # Fetch and display results
#     data = output_sheet.get_all_values()
#     st.write(data)

# min_value = gdp_df['Year'].min()
# max_value = gdp_df['Year'].max()

# from_year, to_year = st.slider(
#     'Which years are you interested in?',
#     min_value=min_value,
#     max_value=max_value,
#     value=[min_value, max_value])

# countries = gdp_df['Country Code'].unique()

# if not len(countries):
#     st.warning("Select at least one country")

# selected_countries = st.multiselect(
#     'Which countries would you like to view?',
#     countries,
#     ['DEU', 'FRA', 'GBR', 'BRA', 'MEX', 'JPN'])

''
''
''

# # Filter the data
# filtered_gdp_df = gdp_df[
#     (gdp_df['Country Code'].isin(selected_countries))
#     & (gdp_df['Year'] <= to_year)
#     & (from_year <= gdp_df['Year'])
# ]

# st.header('GDP over time', divider='gray')

# ''

# st.line_chart(
#     filtered_gdp_df,
#     x='Year',
#     y='GDP',
#     color='Country Code',
# )

''
''


# first_year = gdp_df[gdp_df['Year'] == from_year]
# last_year = gdp_df[gdp_df['Year'] == to_year]

# st.header(f'GDP in {to_year}', divider='gray')

''

# cols = st.columns(4)

# for i, country in enumerate(selected_countries):
#     col = cols[i % len(cols)]

#     with col:
#         first_gdp = first_year[first_year['Country Code'] == country]['GDP'].iat[0] / 1000000000
#         last_gdp = last_year[last_year['Country Code'] == country]['GDP'].iat[0] / 1000000000

#         if math.isnan(first_gdp):
#             growth = 'n/a'
#             delta_color = 'off'
#         else:
#             growth = f'{last_gdp / first_gdp:,.2f}x'
#             delta_color = 'normal'

#         st.metric(
#             label=f'{country} GDP',
#             value=f'{last_gdp:,.0f}B',
#             delta=growth,
#             delta_color=delta_color
#         )
