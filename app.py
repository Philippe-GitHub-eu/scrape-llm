# app.py
import asyncio, json
import streamlit as st
from main import main as scrape_async  # re-use your scraper

st.set_page_config(page_title="scrape-llm", layout="wide")
st.title("scrape-llm (text + images)")

urls_text = st.text_area("URLs (one per line)", height=150, placeholder="https://example.com\nhttps://www.bbc.com/news")
run_btn = st.button("Run")

if run_btn:
    urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
    if not urls:
        st.warning("Add at least one URL.")
    else:
        try:
            with st.status("Scraping...", expanded=False):
                results = asyncio.run(scrape_async(urls))
        except Exception as e:
            st.error(f"❌  {e}")
            st.stop()


        # Show results only if scraping succeeded
        dump = []
        for art in results:
            data = art.model_dump()
            dump.append(data)

            with st.container(border=True):
                st.subheader(data.get("title") or data["url"])
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**URL:** {data['url']}")
                    if data.get("author"):
                        st.write(f"**Author:** {data['author']}")
                    if data.get("published"):
                        st.write(f"**Published:** {data['published']}")
                    if data.get("summary"):
                        st.write(data["summary"])
                with col2:
                    imgs = data.get("images", [])
                    for im in imgs:
                        st.image(im.get("local_path") or im["url"], caption=im.get("caption") or im.get("alt") or "")
        
        # Offer JSON download
        j = json.dumps(dump, ensure_ascii=False, indent=2)
        st.download_button("Download JSON", j, file_name="results.json", mime="application/json")
