import pandas as pd
import os, json
import random

import streamlit as st
import streamlit_survey as ss
from streamlit_gsheets import GSheetsConnection

# -----------------------------------------------------------------------------
# Declare some useful functions.

NUM_IMAGES_TO_SAMPLE = 10
FORMAL_CHARACTERISTIC_NAMES = {
    "image_lighting": "Image Lighting",
    "perspective": "Perspective",
    "image_background": "Image Background",
    "colors": "Color Palette",
    "photography_genre": "Photography Genre",
    "concept": "Concept",
    "depth": "Depth",
    "image_effects": "Image Effects",
    "hair_style": "Hair Style",
    "facial_expression": "Facial Expression",
    "clothing_style": "Clothing Style",
    "clothing_color_palette": "Clothing Color Palette",
    "posing": "Posing",
    "gaze": "Gaze",
    "visible_body_section": "Visible Body Section"
}
CHARACTERISTIC_OPTIONS_DICT = {
    "Photography Genre": ["Architectural", "Candid", "Staged", "Portrait", "Selfie", "Group", "Product", "Fashion", "Beauty", "Bridal", "Interior", "Street", "Landscape", "Sky", "Still-life", "Action", "Underwater", "Botanical", "Historical", "Amateur", "Abstract", "Live stage"],
    "Clothing Style": ["Casual", "Athletic", "Formal", "Business", "Swimwear", "Business casual", "Traditional", "Protective", "Beachwear", "Costume", "Form fitting"],
    "Gaze": ["Forward", "Downward", "Sideways", "Away", "Upward", "Outward", "Engaged"],
    "Posing": ["Standing", "Seated", "Holding", "Leaning", "Active", "Reclined", "Walking", "Stretching", "Dynamic", "Running", "Relaxed", "Confident"],
    "Hair Style": ["Short", "Covered", "Wavy", "Loose", "Varied", "Straight", "Neat", "Ponytail", "Casual", "Tied back", "Flowing", "Curly", "Updo", "Pulled back", "Braided"],
    "Image Lighting": ["Bright", "Dark", "Moderate", "Studio", "Natural", "Soft", "Hard", "Light glare", "Vignette", "Colored", "Light on subject"],
    "Depth": ["Wide angle shot", "Mid shot", "Close up shot", "Macro shot", "Motion blur", "Radial blur", "Gaussian blur", "Fully focused subject", "Unfocused subject", "Partly focused subject", "Bokeh effect", "Isolated focal point", "Multiple focal points", "Bright focal point", "Dark focal point", "Shallow depth of field"],
    "Visible Body Section": ["Upper body", "Full body", "Hand only", "Lower half", "Close up", "Midsection", "Full back", "Head shot"],
    "Perspective": ["Bird eye view", "Worm eye view", "Fish eye view", "Panorama view", "Centered composition", "Rule of third", "Altered perspective", "Framed image", "High angle photo", "Low angle photo", "Vertical composition", "Corner shot", "Point of view shot", "Audience perspective"],
    "Image Background": ["Solid", "Pattern", "Gradient", "Background as frame", "Textured", "Wood", "Blurred", "Transparent", "Bright", "Dark", "Light"],
    "Color Palette": ["Grayscale", "Monotone", "Two tone", "Bright colors", "Pastel colors", "Complementary colors", "Analogous colors", "Inverted colors", "Galaxy colors", "Aquatic colors", "Sunset colors", "Autumnal colors"],
    "Concept": ["Illustration", "Photorealism", "Typography", "Vintage", "Graphic design", "Cartoon", "Incomplete art", "Wave pattern", "Text heavy"],
    "Image Effects": ["Short exposure", "Long exposure", "Neutral density filter", "Artificial shadow", "Silhouette", "Pixelated image", "Vanishing point", "Negative space", "Motion capture", "Cut-out", "Symmetric", "Asymmetry", "Low saturation", "High saturation", "Low contrast", "High contrast"],
    "Facial Expression": ["Engaged", "Content", "Focused", "Neutral", "Joyful", "Relaxed", "Contemplative"],
    "Clothing Color Palette": ["Neutral", "Colorful", "Vibrant", "Monochrome", "Earthy", "Pastel", "Muted"]
}

def get_characteristics_based_upon_JS_divergence(brand1List, brand2List):
    js_data_dict = pd.read_excel(os.path.join("data", "excel", "JSDivergence.xlsx"), sheet_name=None)
    characteristicsList = []
    for brand1, brand2 in zip(brand1List, brand2List):
        brands_list = [brand1.lower(), brand2.lower()]
        listOfJSDiv = []

        for attr in js_data_dict:
            curr_df = js_data_dict[attr]
            curr_df = curr_df[curr_df["brand1"].isin(brands_list) & curr_df["brand2"].isin(brands_list)]
            assert curr_df.shape[0] == 1 # only 1 row for each brand pair
            listOfJSDiv.append((attr, curr_df["JS"].to_list()[0]))
        
        listOfJSDiv.sort(key=lambda x : x[1], reverse=True)
        total_attrs = len(listOfJSDiv)
        answer_chars = listOfJSDiv[:2] + listOfJSDiv[-2:] + listOfJSDiv[total_attrs//2:total_attrs//2+2]
        answer_chars = [FORMAL_CHARACTERISTIC_NAMES[i[0]] for i in answer_chars]
        characteristicsList.append(answer_chars)
    return characteristicsList

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
    brand_im1_folders = questions_df["Brand1ImPath"].to_list()
    # responses1 = [requests.get(im_url.format(img_id), headers={'Authorization': f'Bearer {credentials.token}'})  for img_id in brand_im1_ids]
    # print(resp.status_code for resp in responses1)
    # brand_im1_images = [BytesIO(resp.content) for resp in responses1]

    brand_im1_image_lists = [random.sample(os.listdir(os.path.join("data", "images", fldr)), NUM_IMAGES_TO_SAMPLE) for fldr in brand_im1_folders]
    brand_im1_images = [[os.path.join("data", "images", brand_im1_folders[itr], img_id) for img_id in brand_im1_image_lists[itr]] for itr in range(questions_df.shape[0])]

    # print(type(brand_im1_images[0]))

    brand2_names = questions_df["Brand2"].to_list()
    brand_im2_folders = questions_df["Brand2ImPath"].to_list()
    # responses2 = [requests.get(im_url.format(img_id), headers={'Authorization': f'Bearer {credentials.token}'})  for img_id in brand_im2_ids]
    # print(resp.status_code for resp in responses2)
    # brand_im2_images = [BytesIO(resp.content) for resp in responses2]

    brand_im2_image_lists = [random.sample(os.listdir(os.path.join("data", "images", fldr)), NUM_IMAGES_TO_SAMPLE) for fldr in brand_im2_folders]
    brand_im2_images = [[os.path.join("data", "images", brand_im2_folders[itr], img_id) for img_id in brand_im2_image_lists[itr]] for itr in range(questions_df.shape[0])]

    brand_options = get_characteristics_based_upon_JS_divergence(brand1_names, brand2_names)
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

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='BrandFusion User Survey',
    page_icon=':earth_americas:', # This is an emoji shortcode. Could be a URL too.
)
survey = ss.StreamlitSurvey("User Survey")

if "collected_questions_data" not in st.session_state:
    st.session_state["collected_questions_data"] = False

if not st.session_state["collected_questions_data"]:
    questions_df = get_spreadsheet_data_local()
    st.session_state["questions_df"] = questions_df
    st.session_state["total_questions"] = questions_df.shape[0]
    brand1_names, brand2_names, brand_im1_images, brand_im2_images, brand_options = process_local_questions_data(questions_df)
    st.session_state["brand1_names"] = brand1_names
    st.session_state["brand2_names"] = brand2_names
    st.session_state["brand_im1_images"] = brand_im1_images
    st.session_state["brand_im2_images"] = brand_im2_images
    st.session_state["brand_options"] = brand_options
    st.session_state["collected_questions_data"] = True

# will be used to empty the survey form upon submitting
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
3. Varun Khurana (varunkhurana@adobe.com)\n
4. Yaman Kumar (ykumar@adobe.com)\n
5. Jayakumar Subramanian (jasubram@adobe.com)\n
'''

# Add some spacing
''
''

Agree_Box = ss.CheckBox(survey=survey, label="I fit the eligibility criteria and agree to participate in the survey.", id="Agree_box", value=False)
Second_Title = '''
In each of the following questions, you'll be shown two sets of (advertisement) images from two different brands of the same sector (e.g. 2 Fashion brands, 2 Airlines brands etc.). Then, from a given list of characteristics, you'll need to choose which are the most differentiating characteristics between the two sets of images. Also, you'll need to assign the labels per characteristic which are relevant to each set of images.\n'''
Third_Title = '''
For example: Given the following two sets of images from the brands brand1 and brand2 (sector brands)\n
These images are different in terms of char1 , char2 and char3, because while brand1 images have label1 char1, label2 char2, label3 char3;\n
the images of brand2 on the other hand have label4 char1, label5 char2 and label6 char3.\n
Therefore, one valid response would be char1, char2 and label1, label4 and label2, label5.\n
To get a better understanding of the possible characteristics, we encourage you to look at this doc with example images.
'''

Question_template = '''
Choose 2 most distinctive characteristics between the below sets of images.
'''
Question_components = [ss.MultiSelect(survey=survey, label="Select in order of distinctiveness (most distinctive first):", id=f"Characteristic_component_{itr}", key=f"Characteristic_component_{itr}", options=st.session_state["brand_options"][itr]) for itr in range(st.session_state["total_questions"])]

FollowUp_Question_template = '''
{0} in {1} images'''
# st.session_state["Brand1_FollowUp_Char1_Options"] = [["default"] for _ in range(st.session_state["total_questions"])]
# st.session_state["Brand2_FollowUp_Char1_Options"] = [["default"] for _ in range(st.session_state["total_questions"])]
# st.session_state["Brand1_FollowUp_Char2_Options"] = [["default"] for _ in range(st.session_state["total_questions"])]
# st.session_state["Brand2_FollowUp_Char2_Options"] = [["default"] for _ in range(st.session_state["total_questions"])]
Brand1_FollowUp_Char1_components = [None]*st.session_state["total_questions"]

Brand2_FollowUp_Char1_components = [None]*st.session_state["total_questions"]

Brand1_FollowUp_Char2_components = [None]*st.session_state["total_questions"]

Brand2_FollowUp_Char2_components = [None]*st.session_state["total_questions"]
    
pages = survey.pages(st.session_state["total_questions"]+2, progress_bar=True, on_submit=lambda: store_state_on_submit(survey1=survey))

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
        st.write(Third_Title)
    else:
        if pages.current == pages.n_pages-1:
            with empty_placeholder.container():
                # use empty placeholder only for last page
                st.write(Question_template)
                st.subheader(f"{st.session_state['brand1_names'][pages.current-2]}")
                cols1 = st.columns(NUM_IMAGES_TO_SAMPLE, vertical_alignment="bottom")
                for idx in range(NUM_IMAGES_TO_SAMPLE):
                    cols1[idx].image(st.session_state["brand_im1_images"][pages.current-2][idx], use_container_width=True)
                # st.image(st.session_state["brand_im1_images"][pages.current-2], caption=f"{st.session_state['brand1_names'][pages.current-2]}")
                st.subheader(f"{st.session_state['brand2_names'][pages.current-2]}")
                cols2 = st.columns(NUM_IMAGES_TO_SAMPLE, vertical_alignment="bottom")
                for idx in range(NUM_IMAGES_TO_SAMPLE):
                    cols2[idx].image(st.session_state["brand_im2_images"][pages.current-2][idx], use_container_width=True)
                # st.image(st.session_state["brand_im2_images"][pages.current-2], caption=f"{st.session_state['brand2_names'][pages.current-2]}")
                characteristic_value = Question_components[pages.current-2].display()
                if len(characteristic_value) != 2:
                    st.session_state["selected_chars"] = False
                    st.error(f"Please select 2 options.")
                else:
                    st.session_state["selected_chars"] = True
                    # st.session_state["Brand1_FollowUp_Char1_Options"][pages.current-2] = CHARACTERISTIC_OPTIONS_DICT[characteristic_value[0]]
                    # st.session_state["Brand1_FollowUp_Char2_Options"][pages.current-2] = CHARACTERISTIC_OPTIONS_DICT[characteristic_value[1]]
                    # st.session_state["Brand2_FollowUp_Char1_Options"][pages.current-2] = CHARACTERISTIC_OPTIONS_DICT[characteristic_value[0]]
                    # st.session_state["Brand2_FollowUp_Char2_Options"][pages.current-2] = CHARACTERISTIC_OPTIONS_DICT[characteristic_value[1]]

                    Brand1_FollowUp_Char1_components[pages.current-2] = ss.SelectBox(survey=survey, label=f"Brand1_FollowUp_Char1_component_{pages.current-2}", label_visibility="collapsed", options=CHARACTERISTIC_OPTIONS_DICT[characteristic_value[0]], key=f"Brand1_FollowUp_Char1_component_{pages.current-2}")

                    Brand2_FollowUp_Char1_components[pages.current-2] = ss.SelectBox(survey=survey, label=f"Brand2_FollowUp_Char1_component_{pages.current-2}", label_visibility="collapsed", options=CHARACTERISTIC_OPTIONS_DICT[characteristic_value[0]], key=f"Brand2_FollowUp_Char1_component_{pages.current-2}")

                    Brand1_FollowUp_Char2_components[pages.current-2] = ss.SelectBox(survey=survey, label=f"Brand1_FollowUp_Char2_component_{pages.current-2}", label_visibility="collapsed", options=CHARACTERISTIC_OPTIONS_DICT[characteristic_value[1]], key=f"Brand1_FollowUp_Char2_component_{pages.current-2}")

                    Brand2_FollowUp_Char2_components[pages.current-2] = ss.SelectBox(survey=survey, label=f"Brand2_FollowUp_Char2_component_{pages.current-2}", label_visibility="collapsed", options=CHARACTERISTIC_OPTIONS_DICT[characteristic_value[1]], key=f"Brand2_FollowUp_Char2_component_{pages.current-2}")

                    st.write(FollowUp_Question_template.format(characteristic_value[0], st.session_state["brand1_names"][pages.current-2]))
                    brand1_char1_value = Brand1_FollowUp_Char1_components[pages.current-2].display()

                    st.write(FollowUp_Question_template.format(characteristic_value[0], st.session_state["brand2_names"][pages.current-2]))
                    brand2_char1_value = Brand2_FollowUp_Char1_components[pages.current-2].display()

                    if brand1_char1_value == brand2_char1_value:
                        st.session_state["char1_different"] = False
                        st.error(f"The {characteristic_value[0]} for both the brands should be different!")
                    else:
                        st.session_state["char1_different"] = True

                    st.write(FollowUp_Question_template.format(characteristic_value[1], st.session_state["brand1_names"][pages.current-2]))
                    brand1_char2_value = Brand1_FollowUp_Char2_components[pages.current-2].display()

                    st.write(FollowUp_Question_template.format(characteristic_value[1], st.session_state["brand2_names"][pages.current-2]))
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
            st.subheader(f"{st.session_state['brand1_names'][pages.current-2]}")
            cols1 = st.columns(NUM_IMAGES_TO_SAMPLE, vertical_alignment="bottom")
            for idx in range(NUM_IMAGES_TO_SAMPLE):
                cols1[idx].image(st.session_state["brand_im1_images"][pages.current-2][idx], use_container_width=True)
            # st.image(st.session_state["brand_im1_images"][pages.current-2], caption=f"{st.session_state['brand1_names'][pages.current-2]}")
            st.subheader(f"{st.session_state['brand2_names'][pages.current-2]}")
            cols2 = st.columns(NUM_IMAGES_TO_SAMPLE, vertical_alignment="bottom")
            for idx in range(NUM_IMAGES_TO_SAMPLE):
                cols2[idx].image(st.session_state["brand_im2_images"][pages.current-2][idx], use_container_width=True)
            # st.image(st.session_state["brand_im2_images"][pages.current-2], caption=f"{st.session_state['brand2_names'][pages.current-2]}")
            characteristic_value = Question_components[pages.current-2].display()
            if len(characteristic_value) != 2:
                st.session_state["selected_chars"] = False
                st.error(f"Please select 2 options.")
            else:
                st.session_state["selected_chars"] = True
                # st.session_state["Brand1_FollowUp_Char1_Options"][pages.current-2] = CHARACTERISTIC_OPTIONS_DICT[characteristic_value[0]]
                # st.session_state["Brand1_FollowUp_Char2_Options"][pages.current-2] = CHARACTERISTIC_OPTIONS_DICT[characteristic_value[1]]
                # st.session_state["Brand2_FollowUp_Char1_Options"][pages.current-2] = CHARACTERISTIC_OPTIONS_DICT[characteristic_value[0]]
                # st.session_state["Brand2_FollowUp_Char2_Options"][pages.current-2] = CHARACTERISTIC_OPTIONS_DICT[characteristic_value[1]]

                Brand1_FollowUp_Char1_components[pages.current-2] = ss.SelectBox(survey=survey, label=f"Brand1_FollowUp_Char1_component_{pages.current-2}", label_visibility="collapsed", options=CHARACTERISTIC_OPTIONS_DICT[characteristic_value[0]], key=f"Brand1_FollowUp_Char1_component_{pages.current-2}")

                Brand2_FollowUp_Char1_components[pages.current-2] = ss.SelectBox(survey=survey, label=f"Brand2_FollowUp_Char1_component_{pages.current-2}", label_visibility="collapsed", options=CHARACTERISTIC_OPTIONS_DICT[characteristic_value[0]], key=f"Brand2_FollowUp_Char1_component_{pages.current-2}")

                Brand1_FollowUp_Char2_components[pages.current-2] = ss.SelectBox(survey=survey, label=f"Brand1_FollowUp_Char2_component_{pages.current-2}", label_visibility="collapsed", options=CHARACTERISTIC_OPTIONS_DICT[characteristic_value[1]], key=f"Brand1_FollowUp_Char2_component_{pages.current-2}")

                Brand2_FollowUp_Char2_components[pages.current-2] = ss.SelectBox(survey=survey, label=f"Brand2_FollowUp_Char2_component_{pages.current-2}", label_visibility="collapsed", options=CHARACTERISTIC_OPTIONS_DICT[characteristic_value[1]], key=f"Brand2_FollowUp_Char2_component_{pages.current-2}")

                st.write(FollowUp_Question_template.format(characteristic_value[0], st.session_state["brand1_names"][pages.current-2]))
                brand1_char1_value = Brand1_FollowUp_Char1_components[pages.current-2].display()

                st.write(FollowUp_Question_template.format(characteristic_value[0], st.session_state["brand2_names"][pages.current-2]))
                brand2_char1_value = Brand2_FollowUp_Char1_components[pages.current-2].display()

                if brand1_char1_value == brand2_char1_value:
                    st.session_state["char1_different"] = False
                    st.error(f"The {characteristic_value[0]} for both the brands should be different!")
                else:
                    st.session_state["char1_different"] = True

                st.write(FollowUp_Question_template.format(characteristic_value[1], st.session_state["brand1_names"][pages.current-2]))
                brand1_char2_value = Brand1_FollowUp_Char2_components[pages.current-2].display()

                st.write(FollowUp_Question_template.format(characteristic_value[1], st.session_state["brand2_names"][pages.current-2]))
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
