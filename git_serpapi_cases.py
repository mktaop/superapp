#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 31 13:33:30 2024

@author: avi_patel
"""

import streamlit as st, os, csv, pandas as pd, json, datetime, requests, matplotlib.pyplot as plt
from pytube import YouTube
from serpapi import GoogleSearch
from openai import OpenAI
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def setup():
    st.set_page_config(
        page_title="	✨ Super App",
        layout="centered"
    )
    st.header(":sparkles: Multi Purpose Search and Summarize App", divider='orange')
    
    st.sidebar.header("Options", divider='rainbow')
    
    hide_menu_style = """
            <style>
            #MainMenu {visibility: hidden;}
            </style>
            """
    st.markdown(hide_menu_style, unsafe_allow_html=True)
        

def get_choice():
    chosen = st.sidebar.radio('Select service', [":rainbow[Home]",":blue[YouTube search]",
                                       ":red[Generic search]",":green[Topic search]",":gray[Hotel search]",":violet[Finance search]"]) 
    return chosen


def get_llm():
    tip1="OpenAI model options"
    model=st.sidebar.radio("Choose model:", ["gpt-3.5-turbo-0125","gpt-4o-2024-05-13"], help=tip1)
    return model


def getgptresponse(client, model, temperature, message, streaming):
    try:
        response = client.chat.completions.create(model=model, messages=message, temperature=temperature, stream=streaming)

        output = response.choices[0].message.content
        tokens = response.usage.total_tokens
        yield output, tokens

    except Exception as e:
        print(e)
        yield ""


def remove_punctuation(word):
    new_word = ""
    for letter in word:
        if letter.isalpha() or letter.isdigit() or letter==' ' or letter==',' or letter=='.':
            new_word += letter
    return new_word


def extract_time(date_string):
    time_str = date_string[13:21]  # Adjust slicing as needed
    time_obj = datetime.datetime.strptime(time_str, "%I:%M %p")
    return time_obj.strftime("%H:%M")  # Format as HH:MM (no seconds)


def generate_video(username, password, input_text, source_url):
    url = "https://api.d-id.com/talks"

    payload = {
        "script": {
            "type": "text",
            "subtitles": "false",
            "provider": {
                "type": "microsoft",
                "voice_id": "en-US-JennyNeural"
            },
            "ssml": "false",
            "input": f"{input_text}"
        },
        "config": {
            "fluent": "false",
            "pad_audio": "0.0",
            "driver_expressions": {
                "expressions": [
                    {
                        "start_frame": 0,
                        "expression": "happy",
                        "intensity": 0.75
                    }
                ]
            }
        },
        "source_url": f"{source_url}"
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": 'Basic ' + username + ':' + password
    }

    response = requests.post(url, json=payload, headers=headers)


    
    talk_id = json.loads(response.text)['id']

    talk_url = f"{url}/{talk_id}"

    headers = {
        "accept": "application/json",
        "authorization": 'Basic ' + username + ':' + password
    }

    response = requests.get(talk_url, headers=headers)
    video_response = json.loads(response.text)

    while video_response["status"] != "done":
        response = requests.get(talk_url, headers=headers)
        video_response = json.loads(response.text)

    video_url = video_response["result_url"]
    return video_url



def main():
    """
    1. set up sidebar options
    2. options for: type of service including home, llm model, temperature, tokens, etc
    3. with change to the selection in the side bar, executure on each of the services

    Returns
    -------
    None.

    """
    
    #setup()
    chosen = get_choice()
    model = get_llm()
    
    if chosen==":rainbow[Home]":
        info='''
        This app uses SERP API to scrape results of a google search and youtube search.  
        We take the URL or video you select from the search and scrape that site/video.  
        We will then take the scraped content and ask a LLM to summarize it for you.
        On the left sidebar, there are several choices for search. Select the one that interests you.  
          
        
        __Choices:__  
        1.) Home - Default, it will show you what you are currently seeing.  
        2.) YouTube search - Based on your search input, app will give you choices to select from.  
        3.) Generic search - Type in a generic search as you would intend to on google.com  
        4.) Topic search - Unlike in #3, here you will select from a list of topics.  
        5.) Hotel search - Here, you will enter something like "bali resorts".  
        6.) Finance search - Enter a stock symbol to retrieve quote and news.
        '''
        st.markdown(info)

    elif chosen==":blue[YouTube search]":
        st.subheader("YouTube Search & Summarize.", divider='blue')
        yt_url = st.text_input("Enter search term for YouTube search and hit enter.")
        if yt_url:
            params = {
                      "engine": "youtube",
                      "search_query": f'{yt_url}',
                      "api_key": f'{SERP_API_KEY}',
                      "num":  "10"
                    }

            search = GoogleSearch(params)
            results = search.get_dict()
            yt_results = results["video_results"]
            
            with open('/Users/Documents/serpapi_ytresults.csv', 'w', newline='') as csvfile:
            	csv_writer = csv.writer(csvfile)
            	
            	csv_writer.writerow(["Title", "Link", "Length", "Published_date"])
            	
            	for result in yt_results:
            		csv_writer.writerow([result["title"], result["link"], result["length"], 
                                   result["published_date"]])
            df_yt = pd.read_csv('/Users/Documents/serpapi_ytresults.csv', index_col=0)
            st.write("Top 10 results from the search, copy the url of the video of interest:")
            st.dataframe(df_yt.head(10))
            st.divider()
            st.write("We will need the url from above list for the video you want a LLM to summarize the content of the video")
            yt_url=st.text_input("Paste the YouTube URL or URLs you want to download audio for, separate URL with a space. And hit enter.")
            if yt_url:
                urls = yt_url.split(' ')
                zlen = len(urls)
                transcripts=[]
                for i in range(zlen):
                    yt_url3 = urls[i]
                    yt = YouTube(f'{yt_url3}')
                    yt.streams.filter(only_audio=True).first().download(filename='/Users/Documents/trialmp.mp4')
                    
                    audio_file = open("/Users/Documents/trialmp.mp4", "rb")
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        response_format="text",  
                        file=audio_file
                    )
                    transcripts.append(transcript)
                
                #model = get_llm()
                prompt = st.text_input("Enter prompt for LLM, e.g. Summarize the following youtube transcripts.")
                if prompt:
                    message=[]
                    message.append({"role": "system", "content": f"{prompt}"})
                    message.append({"role": "user", "content": f"{transcripts}"})
                    for result in getgptresponse(client, model, temperature=0, message=message, streaming=False):
                        output = result[0]
                        st.write(output)
                    
    elif chosen==":red[Generic search]":
        st.subheader("Google Search & Summarize.", divider='red')
        search_query = st.text_input("Please enter your Google search (e.g. what is hedge fund?) and hit enter.")
        if search_query:
            search_resp = GoogleSearch({
                "q": f'{search_query}', 
                "hl": "en",
                "gl": "us",
                "api_key": f'{SERP_API_KEY}',
                "num":  "5"
              })
            results2 = search_resp.get_dict()
            organic_results = results2["organic_results"]
            
            with open('/Users/Documents/serpapi_srchresults.csv', 'w', newline='') as csvfile:
            	csv_writer = csv.writer(csvfile)
            	
            	csv_writer.writerow(["Position", "Title", "Link", "Snippet"])
            	
            	for result in organic_results:
            		csv_writer.writerow([result["position"], result["title"], result["link"], result["snippet"]])
            df_srch = pd.read_csv('/Users/Documents/serpapi_srchresults.csv', index_col=0)
            st.write("Top 5 results from the search, copy the url of the video of interest:")
            st.dataframe(df_srch.head(5))
            st.divider()
            
            st.write("We will need the url from above list that you want a LLM to summarize the content of that website.")
            search_url=st.text_input("Paste the URL or URLS separated by a space that you want to scrape content from. And hit enter.")
            if search_url:
                urls = search_url.split(' ')
                zlen = len(urls)
                transcripts=[]
                for i in range(zlen):
                    yt_url3 = urls[i]
                    loader = WebBaseLoader(f'{yt_url3}')
                    docs = loader.load()
                    text_splitter = RecursiveCharacterTextSplitter()
                    splits = text_splitter.split_documents(docs)
                    totaldoc="".join(doc.page_content for doc in splits)
                    totaldoc2=remove_punctuation(totaldoc)
                    transcripts.append(totaldoc2)
                
                #model = get_llm()
                temperature=0
                streaming=False
                prompt1 = st.text_input("Enter your prompt or quesiton related to the website content for LLM to answer.")
                if prompt1:
                    message2=[]
                    message2.append({"role": "user", "content": f"{prompt1}"})
                    message2.append({"role": "user", "content": f"{transcripts}"})
                    for result in getgptresponse(client, model, temperature=temperature, message=message2, streaming=streaming):
                        output2 = result[0]
                        choice_output = st.radio(
                            "How do you want to see the output?",
                            ["View the text copy", "Read out by a talking head"],
                            index=None, horizontal=True,
                        )
                        if choice_output == None:
                            pass
                        elif choice_output=="View the text copy":
                            st.write(output2)
                        elif choice_output=="Read out by a talking head":
                            img = "" #insert url to your image or upload one from your local directory
                            split_key = DID_API_KEY.split(':')
                            username = split_key[0]
                            password = split_key[1]
                            video_url = generate_video(username, password, output2, img)
                            st.video(video_url)
                        
    elif chosen==":green[Topic search]":
        st.subheader("Google News Topics & Summarize.", divider='green')
        topic_select = st.selectbox('Which of the following topics you want to retrieve news headlines for?',
                              ('','Business', 'Technology', 'Sports'))
        if topic_select != '':
            topic_resp = GoogleSearch({
                "q": f"{topic_select}",
                "tbm": "nws",
                "hl": "en",
                "gl": "us",
                "num":  "7",
                "api_key": f'{SERP_API_KEY}',
              })
            results3 = topic_resp.get_dict()
            topic_results = results3["news_results"]
            
            with open('/Users/Documents/serpapi_topicresults.csv', 'w', newline='') as csvfile:
            	csv_writer = csv.writer(csvfile)
            	
            	# Write the headers
            	csv_writer.writerow(["Position", "Title", "Link", "Snippet"])
            	# Write the data
            	for result in topic_results:
            		csv_writer.writerow([result["position"], result["title"], result["link"], result["snippet"]])
            df_srch = pd.read_csv('/Users/Documents/serpapi_topicresults.csv', index_col=0)
            st.write("Top 7 results from the search based on your topic, copy the url of the video of interest:")
            st.dataframe(df_srch.head(7))
            st.divider()
            
            st.write("We will need the url from above list that you want a LLM to summarize the content of that website.")
            search_url=st.text_input("Paste the URL or URLS separated by a space that you want to scrape content from. And hit enter.")
            if search_url:
                urls = search_url.split(' ')
                zlen = len(urls)
                transcripts=[]
                for i in range(zlen):
                    yt_url3 = urls[i]
                    loader = WebBaseLoader(f'{yt_url3}')
                    docs = loader.load()
                    text_splitter = RecursiveCharacterTextSplitter()
                    splits = text_splitter.split_documents(docs)
                    totaldocb="".join(doc.page_content for doc in splits)
                    totaldocb2=remove_punctuation(totaldocb)
                    transcripts.append(totaldocb2)
                
                #model = get_llm()
                temperature=0
                streaming=False
                prompt2 = st.text_input("Enter your prompt or quesiton related to the website content for LLM to answer.")
                if prompt2:
                    message3=[]
                    message3.append({"role": "user", "content": f"{prompt2}"})
                    message3.append({"role": "user", "content": f"{transcripts}"})
                    for result in getgptresponse(client, model, temperature=temperature, message=message3, streaming=streaming):
                        output3 = result[0]
                        st.write(output3)
        else:
            pass
        
    elif chosen == ":gray[Hotel search]":
        st.subheader("Search for Hotels/Resorts and summarize.", divider='gray')
        search_query2 = st.text_input("Please enter name of island/place (e.g. Bali Resorts) to search for hotels/resorts.")
        if search_query2:
            checkin = st.text_input("Please enter the check in date (e.g. 2024-06-25) and hit enter.")
            if checkin:
                checkout = st.text_input("Please enter the check out date (e.g. 2024-07-06) andh it enter.")
                if checkout:
                    guests = st.text_input("Please enter number of guests (e.g. 2) and hit enter")
                    if guests:
                        params2 = {
                          "engine": "google_hotels",
                          "q": f"{search_query2}",
                          "check_in_date": f"{checkin}",
                          "check_out_date": f"{checkout}",
                          "adults": f"{guests}",
                          "currency": "USD",
                          "gl": "us",
                          "hl": "en",
                          "num": "7",
                          "api_key": f'{SERP_API_KEY}'
                        }
                        search2 = GoogleSearch(params2)
                        results = search2.get_dict()
                        hotel_results = results["properties"]
                        shortlist = hotel_results[0:7]    
                        json_string = json.dumps(shortlist)
                        #model = get_llm()
                        temperature=0
                        streaming=False
                        prompt3 = st.text_input("Enter your prompt or question.")
                        if prompt3:
                            getsummary = st.button("Get Results")
                            if getsummary:
                                message4=[]
                                message4.append({"role": "user", "content": f"{prompt3}"})
                                message4.append({"role": "user", "content": f"{json_string}"})
                                for result in getgptresponse(client, model, temperature=temperature, message=message4, streaming=streaming):
                                    output4 = result[0]
                                    choice_output = st.radio(
                                        "How do you want to see the output?",
                                        ["View the text copy", "Read out by a talking head"],
                                        index=None, horizontal=True,
                                    )
                                    if choice_output == None:
                                        pass
                                    elif choice_output=="View the text copy":
                                        st.write(output4)
                                    elif choice_output=="Read out by a talking head":
                                        img = "" #inser url to your image or import from local directory
                                        split_key = DID_API_KEY.split(':')
                                        username = split_key[0]
                                        password = split_key[1]
                                        video_url2 = generate_video(username, password, output4, img)
                                        st.video(video_url2)

                                
    elif chosen == ":violet[Finance search]":
        st.subheader("Get most current quote and a graph.", divider='violet')
        st.text("Provide a stock symbol with the exchange; e.g., AMZN:NASDAQ.")
        quote = st.text_input("Your input remember to provide both the symbol and the exchange!")
        if quote:
            params = {
              "engine": "google_finance",
              "q": "AMZN:NASDAQ",

              "api_key": f'{SERP_API_KEY}'
            }

            search = GoogleSearch(params)
            resultsz = search.get_dict()
            graph_results = resultsz["graph"]
            stck_price=resultsz["summary"]["price"]
            movement = resultsz["summary"]["price_movement"]["movement"]
            value = resultsz["summary"]["price_movement"]["value"]
            
            stock_info = "The last or closing price is {} which is {} by {}.".format(stck_price, movement, value)
            st.write(stock_info)
            st.write("Following is the daily chart:")
            
            with open('/Users/Documents/serpapi1z4.csv', 'w', newline='') as csvfile:
            	csv_writer = csv.writer(csvfile)
            	
            	# Write the headers
            	csv_writer.writerow(["date",  "price"])
            	
            	# Write the data
            	for result in graph_results:
            		csv_writer.writerow([result["date"], result["price"]])
            
            df = pd.read_csv('/Users/Documents/serpapi1z4.csv')
            df['date'] = df['date'].apply(extract_time)

            plt.plot(df['date'], df['price'])
            plt.xlabel("Time")
            plt.ylabel("Price")
            plt.title("Price vs. Time")
            plt.xticks(df['date'][::30])
            plt.xticks(rotation=45) 
            fig = plt.gcf()
            st.pyplot(fig)
            
        
                    

if __name__ == '__main__':
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    client = OpenAI(api_key=OPENAI_API_KEY)
    SERP_API_KEY = os.environ.get('SERPAPI_KEY')
    DID_API_KEY = os.environ.get('DID_API_KEY')
    setup()
    main()