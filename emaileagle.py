import streamlit as st
import pandas as pd
import requests
import requests.exceptions
import urllib.parse
from collections import deque
import re
from bs4 import BeautifulSoup

# Function to scrape emails and URLs
def scrape_emails_and_urls(user_url, max_urls=50):
    urls = deque([user_url])
    scraped_urls = set()
    emails = set()
    count = 0
    while len(urls):
        count += 1
        if count == int(max_urls):
            break
        url = urls.popleft()
        scraped_urls.add(url)
        parts = urllib.parse.urlsplit(url)
        base_url = '{0.scheme}://{0.netloc}'.format(parts)
        path = url[:url.rfind('/')+1] if '/' in parts.path else url
        try:
            response = requests.get(url)
        except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
            continue
        new_emails = set(re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", response.text, re.I))
        emails.update(new_emails)
        soup = BeautifulSoup(response.text, features="lxml")
        for anchor in soup.find_all("a"):
            link = anchor.attrs['href'] if 'href' in anchor.attrs else ''
            if link.startswith('/'):
                link = base_url + link
            elif not link.startswith('http'):
                link = path + link
            if link not in urls and link not in scraped_urls:
                urls.append(link)
    return emails, scraped_urls

# Function to convert data to CSV format
@st.cache_data
def convert_to_csv(data):
    return pd.DataFrame(data).to_csv(index=False).encode('utf-8')

# Streamlit interface
st.title("EmailEagle - Best Email and URL Scraper")
user_url = st.text_input("Enter Main Target URL To Scan:")
max_urls = st.text_input("Enter max_sub urls: (default: 50)")

if st.button("Start Scraping"):
    with st.spinner("Scraping...It may take some time depending on the number of sub-URLs."):
        emails, scraped_urls = scrape_emails_and_urls(user_url, max_urls)
        max_length = max(len(emails), len(scraped_urls))
        emails = list(emails)  # Convert set to list
        scraped_urls = list(scraped_urls)  # Convert set to list
        emails += [''] * (max_length - len(emails))
        scraped_urls += [''] * (max_length - len(scraped_urls))
        data = {"Emails": emails, "URLs": scraped_urls}
        df = pd.DataFrame(data)
        csv_data = convert_to_csv(df)
        st.success("Scraping done!")

    st.download_button(
        label="Download Emails and URLs as CSV",
        data=csv_data,
        file_name='EmailEagle.csv',
        mime='text/csv',
        key='download-csv'
    )
