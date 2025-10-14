import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import concurrent.futures
import time

warnings.filterwarnings('ignore')

# Import the Python SDK
import google.generativeai as genai
# Used to securely store your API key
# from google.colab import userdata # Commented out as per request

# GOOGLE_API_KEY=userdata.get('GOOGLE_API_KEY') # Commented out as per request
GOOGLE_API_KEY="AIzaSyBm5bwUn44kQQExgAVamMqgvInUu7A-RGg" # Placeholder for explicit API key
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize the Gemini API
gemini_model = genai.GenerativeModel('gemini-2.0-flash')

# Global variables
## single content corpus
keywords = ['hufagrip','hufagripp'] # for scraping target & explicit data cleansing
topics = [] # for corpus-level topics analysis

## personality corpus
interests = [] # for audience-level profiling analysis
communication_styles = ['formal','informal'] # for audience-level profiling analysis
author_personality = [] # for audience-level profiling analysis
values = [] # for audience-level profiling analysis

"""## Functions Declaration"""

# Analysis Functions
# This code block is for declaring functions related to analysis & meta-analysis functions of text-based, and visual-based data.

############################################################################ Remove Data With Duplicated Texts ############################################################################

def remove_duplicates(data,platform):
    # removes duplicates in id_list list
    unique_data = []
    for datum in data:
        if datum not in unique_data:
            unique_data.append(datum)
    return unique_data

############################################################################ Language-based cleansing ############################################################################

def explicit_keywords_cleansing(data,keywords) :
    # Data is a list of texts
    # Removes members of the Data list that do not contain any of the keywords
    cleaned_data = []
    for text in data:
        # Add a check to ensure the item is a string before calling .lower()
        if isinstance(text, str) and any(keyword.lower() in text.lower() for keyword in keywords):
            cleaned_data.append(text)
    return cleaned_data

############################################################################ Language-based cleansing ############################################################################

def language_based_cleansing(batch_data) :
    # Seed prompt
    language_seed_prompt = "Evaluate the following text. Return FALSE if the text's language in general is Indonesian or dialects spoken in indonesia. Otherwise return TRUE if it's not in Indonesian language or dialects spoken in Indonesia. Respond with only TRUE or FALSE"

    def get_language_decision(text):
        prompt = f"{language_seed_prompt} Text: {text}"
        retries = 0
        while retries < 3:
            try:
                response = gemini_model.generate_content(prompt)
                if response and response.text:
                    decision = response.text.strip().upper()
                    return (decision, text)
                return ('ERROR', text)
            except Exception as e:
                retries += 1
                if retries >= 3:
                    return ('ERROR', text)
                time.sleep(1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(get_language_decision, batch_data))

    cleaned_data = []
    for decision, original_text in results:
        if decision == "FALSE":
            cleaned_data.append(original_text)

    return cleaned_data

############################################################################ Sentiment Analysis ############################################################################

def sentiment_analysis(batch_data) :
    # Seed prompt
    sentiment_seed_prompt = "Analyze the sentiment of the following text and classify it as 'Positive', 'Negative', or 'Neutral'. Respond only with one of these three words."

    def get_sentiment(text):
        prompt = f"{sentiment_seed_prompt} Text: {text}"
        retries = 0
        while retries < 3:
            try:
                response = gemini_model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
                return 'Neutral'
            except Exception as e:
                retries += 1
                if retries >= 3:
                    return 'Neutral'
                time.sleep(1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        sentiments = list(executor.map(get_sentiment, batch_data))

    return sentiments


############################################################################ Topic Analysis ############################################################################

def topic_analysis(batch_data, topics) :
    # Seed prompt
    topic_seed_prompt = f"""Analyze the following text and infer its main topic.

    Consider the following existing topic labels: {topics}

    If the text's topic is closely related to one of the existing labels, return that label.
    If the text's topic is unique and does not closely approximate any of the existing labels, invent a new, concise topic label (2-4 words) and return ONLY the new label.

    Respond only with an existing or a new topic label."""

    def get_topic(text):
        prompt = f"{topic_seed_prompt} Text: {text}"
        retries = 0
        while retries < 3:
            try:
                response = gemini_model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
                return 'Unknown'
            except Exception as e:
                retries += 1
                if retries >= 3:
                    return 'Unknown'
                time.sleep(1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        identified_topics = list(executor.map(get_topic, batch_data))

    for topic in identified_topics:
        if topic not in topics and topic != 'Unknown':
            topics.append(topic)

    return identified_topics

############################################################################ Interest Analysis ############################################################################

def interest_analysis(batch_data, interests) :
    # Seed prompt
    interest_seed_prompt = f"""Analyze the following text and infer the user's interests.

    Consider the following existing interest labels: {interests}
    If the user's interest is closely related to one of the existing labels, return that label.
    If the user's interest is unique and does not closely approximate any of the existing labels, invent a new, concise interest label (2-4 words) and return ONLY the new label.

    Respond only with an existing or a new interest label."""

    def get_interest(text):
        prompt = f"{interest_seed_prompt} Text: {text}"
        retries = 0
        while retries < 3:
            try:
                response = gemini_model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
                return 'Unknown'
            except Exception as e:
                retries += 1
                if retries >= 3:
                    return 'Unknown'
                time.sleep(1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        identified_interests = list(executor.map(get_interest, batch_data))

    for interest in identified_interests:
        if interest not in interests and interest != 'Unknown':
            interests.append(interest)

    return identified_interests

############################################################################ Communication Style Analysis ############################################################################

def communication_style_analysis(batch_data, communication_styles) :
    # Seed prompt
    communication_style_seed_prompt = f"""Analyze the following text and classify the user's communication style.

    Consider the following existing communication styles: {communication_styles}
    Classify the user's communication style as one of these labels.

    Respond only with a communication style label."""

    def get_style(text):
        prompt = f"{communication_style_seed_prompt} Text: {text}"
        retries = 0
        while retries < 3:
            try:
                response = gemini_model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
                return 'Unknown'
            except Exception as e:
                retries += 1
                if retries >= 3:
                    return 'Unknown'
                time.sleep(1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        identified_styles = list(executor.map(get_style, batch_data))

    return identified_styles

############################################################################ Values Analysis ############################################################################

def values_analysis(batch_data, values) :
    # Seed prompt
    values_seed_prompt = f"""Analyze the following text and infer the user's values.

    Consider the following existing value labels: {values}
    If the user's value is closely related to one of the existing labels, return that label.
    If the user's value is unique and does not closely approximate any of the existing labels, invent a new, concise value label (2-4 words) and return ONLY the new label.

    Respond only with an existing or a new value label."""

    def get_value(text):
        prompt = f"{values_seed_prompt} Text: {text}"
        retries = 0
        while retries < 3:
            try:
                response = gemini_model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
                return 'Unknown'
            except Exception as e:
                retries += 1
                if retries >= 3:
                    return 'Unknown'
                time.sleep(1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        identified_values = list(executor.map(get_value, batch_data))

    for value in identified_values:
        if value not in values and value != 'Unknown':
            values.append(value)

    return identified_values

############################################################################ Dataframe Update ############################################################################

def dataframe_udate(df, data, platform, layer):
    """
    Updates the dataframe to keep only the rows where the text data
    (caption for instagram) is present in the provided 'data' list.
    """

    if layer == 1 :
        if platform == 'tiktok' or platform == 'youtube':
            df = df[df['title'].isin(data)].reset_index(drop=True)
        elif platform == 'twitter':
            df = df[df['text'].isin(data)].reset_index(drop=True)
        elif platform == 'instagram':
            df = df[df['caption'].isin(data)].reset_index(drop=True)
    elif layer == 2 :
        df = df[df['text'].isin(data)].reset_index(drop=True)
    return df

"""## Execution Block

### Layer 1 execution

This layer deals with the first layer of scraped data i.e. Instagram, TikTok, Twitter posts.

This section returns the cleansed urls to be processed by the data scraper, since data scraper takes urls as input
"""

import pandas as pd

############################################################################ INPUTS ############################################################################
case_name = 'hufagripp'
file_path = 'dataset_tiktok-scraper_hufagripp.json'
platform = 'tiktok'
layer = 1
############################################################################ DATA READING & PRE-PROCESSING ############################################################################

# Choose method depending on filetype
if file_path.endswith('.csv'):
    df = pd.read_csv(file_path)
elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
    df = pd.read_excel(file_path)
elif file_path.endswith('.json'):
    df = pd.read_json(file_path)
else:
    print("Unsupported file type. Please provide a CSV, Excel, or JSON file.")

# Specifically for instagram, unpacks the topPosts and make the dataframe to be about them
if platform == 'instagram' :
  df = df.explode('topPosts')
  df = pd.json_normalize(df['topPosts'])
  # remove topPosts with identical ids
  df = df.drop_duplicates(subset=['id'])
  df = df.reset_index(drop=True)

# For TikTok: Rename columns to match expected format
if platform == 'tiktok':
  # Rename 'text' to 'title' if 'title' doesn't exist
  if 'title' not in df.columns and 'text' in df.columns:
    df['title'] = df['text']
  # Rename 'webVideoUrl' to 'postPage' if 'postPage' doesn't exist
  if 'postPage' not in df.columns and 'webVideoUrl' in df.columns:
    df['postPage'] = df['webVideoUrl']
  # Create 'description' column if it doesn't exist (use 'text' as fallback)
  if 'description' not in df.columns:
    if 'text' in df.columns:
      df['description'] = df['text']
    else:
      df['description'] = ''

# Display the dataframe
print("\n" + "="*80)
print("DATAFRAME AWAL:")
print("="*80)
print(df.head())
print(f"\nTotal rows: {len(df)}")
print(f"Columns: {list(df.columns)}")

############################################################################ DATA PRE-PROCESSING ############################################################################

# Coerce all text-based data to be string datatype
if platform == 'tiktok' or platform == 'youtube' :
  df['description'] = df['description'].astype(str)
elif platform == 'twitter' :
  df['text'] = df['text'].astype(str)
elif platform == 'instagram' :
  df['caption'] = df['caption'].astype(str)

# The column to be parsed in analysis functions :
# Instagram & twitter columns are usually 'text' while tiktok is 'title'

def data_selection(df) :
  if platform == 'tiktok' or platform == 'youtube' :
    data = df['title'].tolist() # Convert to list
  elif platform == 'twitter':
    data = df['text'].tolist() # Convert to list
  elif platform == 'instagram':
    data = df['caption'].tolist() # Convert to list
  return data

# updates dataframe to remove rows that are not in data
# this function is already defined in MzelE83tCCGM, no need to redefine it here.
# def dataframe_udate(df,data,platform) :
#   if platform == 'tiktok' or platform == 'youtube' :
#     df = df[df['title'].isin(data)]
#     df = df.reset_index(drop=True)
#   elif platform == 'twitter':
#     df = df[df['text'].isin(data)]
#     df = df.reset_index(drop=True)
#   elif platform == 'instagram':
#     df = df[df['caption'].isin(data)]
#     df = df.reset_index(drop=True)
#   return df

############################################################################ CLEANSING ############################################################################

# Run remove duplicates then update dataframe
data = data_selection(df)
data = remove_duplicates(data,platform)
df = dataframe_udate(df,data,platform,1)
print(f'Length of dataframe after duplicates remvoal : {len(df)}')

# Run explicit keywords cleansing then update dataframe
data = data_selection(df)
data = explicit_keywords_cleansing(data,keywords)
df = dataframe_udate(df,data,platform,1)
print(f'Length of dataframe after keywords cleansing : {len(df)}')

# Run language-based cleansing then update dataframe
data = data_selection(df)
data = language_based_cleansing(data)
df = dataframe_udate(df,data,platform,1)
print(f'Length of dataframe after language cleansing : {len(df)}')

print("\n" + "="*80)
print("DATAFRAME SETELAH CLEANSING:")
print("="*80)
print(df.head(10))
print(f"\nTotal rows: {len(df)}")

############################################################################ ANALYSIS ############################################################################

# Divides data into batches
max_data_per_batch = 100
batches = [data[i:i + max_data_per_batch] for i in range(0, len(data), max_data_per_batch)]

# Runs sentiment analysis, batch by batch
all_sentiments = []
for batch in batches:
    sentiments = sentiment_analysis(batch)
    all_sentiments.extend(sentiments)

# Runs topic analysis, batch by batch
all_topics = []
for batch in batches:
    topics_batch = topic_analysis(batch, topics) # Pass the global topics list
    all_topics.extend(topics_batch)

# Add results back to the dataframe
df['sentiment'] = all_sentiments
df['topic'] = all_topics

# Save file for download
# Names the file based on platform name + case_name + layer 1
file_name = platform + '_' + case_name + '_layer1.csv'
df.to_csv(file_name, index=False)

# Display the dataframe
print("\n" + "="*80)
print("HASIL AKHIR LAYER 1 (dengan Sentiment & Topic Analysis):")
print("="*80)
print(df.head(10))
print(f"\nFile saved: {file_name}")
print(f"Total rows: {len(df)}")

# Exit after Layer 1 is complete
print("\n" + "="*80)
print("LAYER 1 SELESAI!")
print("="*80)
print("Untuk menjalankan Layer 2 (Input Generator & Analysis), silakan comment out sys.exit() di bawah ini")
print("dan pastikan file path layer 2 sudah benar.")
import sys
sys.exit(0)

"""### Input Generator"""

import pandas as pd

############################################################################ INPUTS ############################################################################
case_name = 'hufagrip'
file_path = '/content/tiktok_hufagrip_layer1.csv'
platform = 'tiktok'
objects = 'replies/comments'
############################################################################ DATA READING & PRE-PROCESSING ############################################################################

df = pd.read_csv(file_path)

# Returns list of urls
# if platform == 'instagram' or 'twitter':
#   for url in df['url']:
#     print(url)
# elif platform == 'tiktok':
#   for url in df['postPage']:
#     print(url)

for url in df['postPage']:
  print(url)

"""### Analysis"""

import pandas as pd

############################################################################ INPUTS ############################################################################
case_name = 'hufagrip'
file_path = '/content/hufagrip_instagram_comments_2025-09-16_05-58-02-861.json'
platform = 'instagram'
objects = 'comments'
layer = 2
############################################################################ DATA READING & PRE-PROCESSING ############################################################################

# Choose method depending on filetype
if file_path.endswith('.csv'):
    df = pd.read_csv(file_path)
elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
    df = pd.read_excel(file_path)
elif file_path.endswith('.json'):
    df = pd.read_json(file_path)
else:
    print("Unsupported file type. Please provide a CSV, Excel, or JSON file.")

# Display the dataframe
print("\n" + "="*80)
print("DATAFRAME LAYER 2:")
print("="*80)
print(df.head())
print(f"\nTotal rows: {len(df)}")

############################################################################ DATA PRE-PROCESSING ############################################################################

# Coerce all text-based data to be string datatype
if platform == 'tiktok' or platform == 'youtube' :
  df['text'] = df['text'].astype(str)
elif platform == 'twitter' :
  df['text'] = df['text'].astype(str)
elif platform == 'instagram' :
  df['text'] = df['text'].astype(str)

# The column to be parsed in analysis functions :
# Instagram & twitter columns are usually 'text' while tiktok is 'title'

def data_selection(df) :
  if platform == 'tiktok' or platform == 'youtube' :
    data = df['text'].tolist() # Convert to list
  elif platform == 'twitter':
    data = df['text'].tolist() # Convert to list
  elif platform == 'instagram':
    data = df['text'].tolist() # Convert to list
  return data

############################################################################ CLEANSING ############################################################################

# Run remove duplicates then update dataframe
data = data_selection(df)
data_temp = remove_duplicates(data,platform)
df = dataframe_udate(df,data_temp,platform,layer)
print(f'Length of dataframe after duplicates remvoal : {len(df)}')

############################################################################ ANALYSIS ############################################################################

# Divides data into batches
max_data_per_batch = 100
batches = [data[i:i + max_data_per_batch] for i in range(0, len(data), max_data_per_batch)]

# Runs sentiment analysis, batch by batch
all_sentiments = []
for batch in batches:
    sentiments = sentiment_analysis(batch)
    all_sentiments.extend(sentiments)

# Runs topic analysis, batch by batch
all_topics = []
for batch in batches:
    topics_batch = topic_analysis(batch, topics) # Pass the global topics list
    all_topics.extend(topics_batch)

# Add results back to the dataframe
df['sentiment'] = all_sentiments
df['topic'] = all_topics

# Save file for download
# Names the file based on platform name + case_name + layer 2
file_name = platform + '_' + case_name + '_' + objects + '_layer2.csv'
df.to_csv(file_name, index=False)

# Display the dataframe
print("\n" + "="*80)
print("HASIL AKHIR LAYER 2 (dengan Sentiment & Topic Analysis):")
print("="*80)
print(df.head(10))
print(f"\nFile saved: {file_name}")
print(f"Total rows: {len(df)}")

# Validation
print("\n" + "="*80)
print("VALIDASI DATA:")
print("="*80)
print(f"Total sentiments: {len(all_sentiments)}")
print(f"Total topics: {len(all_topics)}")
print(f"Total rows in dataframe: {len(df)}")
print("\nSample data:")
print(df.head(10))