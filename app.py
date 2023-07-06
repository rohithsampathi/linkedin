from flask import Flask, render_template, request
import openai
from newspaper import Article
import concurrent.futures
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from sqlalchemy import func

app = Flask(__name__)

# Initialize GPT-3.5 API
openai.api_key = "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"

@app.route('/')
def home():
    return render_template('index.html')

Base = declarative_base()

class GptTokenUsage(Base):
    __tablename__ = 'token_usage'
    id = Column(Integer, primary_key=True)
    generation_tokens = Column(Integer, nullable=False)
    summary_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# Path to the SQLite file
db_file = 'sqlite:///token_usage.db'

# Creating engine and binding it to the Base class
engine = create_engine(db_file)
Base.metadata.create_all(engine)

# Create a session to access the database
Session = sessionmaker(bind=engine)

@app.route('/generate', methods=['POST'])
def generate():
    urls = request.form.get('news')

    if not urls:
        return {"error": "No URLs provided"}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        article_contents = list(executor.map(process_url, urls.split(",")))

    # Process each article with GPT
    summaries_and_token_counts = [process_with_gpt(content) for content in article_contents]

    # Separate summaries and token counts
    summaries, token_counts = zip(*summaries_and_token_counts)
    total_token_count = sum(token_counts)

    newsout = "\n\n".join(f"News:\n{summary}" for summary in summaries)

    # GPT-3 processing with newsout as input
    writing_style = f"""
    You are montaigne a social GPT who mastered making linkedin posts in Steve Jobs Product Launch style. You will build a persuasive and informative LinkedIn Post from the below provided news. The purpose of the post is to announce the news, and its implication on the market. From there, you should convince the user to visit DataM report for detailed insights about the market. Keep the tone professional and simple. Target audience are CXOs, business decision makers and Investors.

    Must Follows:
    1. Do not sell DataM product more. Make the selling subtle and post more informative
    2. Do not Use magical words and jargon

    Example Post:
    Exciting developments in India's burgeoning pet care industry! Congratulations to Drools Pet Food Pvt. Ltd., a homegrown market leader, for securing a monumental $60M investment from the world's premier consumer growth investor, L Catterton. This partnership represents not only a significant milestone for Drools and the Indian pet care sector but also a strong validation of the company's forward-thinking approach to pet nutrition.

    Drools has admirably captured a staggering 38% of India's pet food market, and with this fresh infusion of funds, the company is poised for strategic expansion - in both product lines and markets. Their steadfast dedication to manufacturing high-quality pet food products has set new industry benchmarks and helped them earn an enviable position among discerning pet parents.

    One of the critical implications of this investment is the potential acceleration of growth in the pet care market across the country, particularly in metros and Tier I & II cities. This advancement is not only a nod to the brand's commitment to serve pet parents but also an indication of India's burgeoning pet care market that is at a crucial inflection point.

    For the curious minds and decision-makers seeking to understand the finer details and market trends, exploring the latest DataM report that provides comprehensive insights into the evolving landscape, giving you an informed edge in your strategic planning. Please note, the intention is not to sell the report but to emphasize its utility as a potent tool in your decision-making arsenal.

    In the spirit of innovation and progressive growth, here's to new partnerships and game-changing developments in the pet food industry! Cheers to Drools and L Catterton on their collaboration, and we eagerly anticipate their future accomplishments.

    #Investment #PetCareIndustry #MarketGrowth #StrategicPartnership

    ------------------- End of Instructions. News below -------------------

   """
    # GPT-3.5-turbo chat model processing with newsout as input
    print("Processing the Post Content with Advanced AI")
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": f"{writing_style}",
            },
            {
                "role": "user",
                "content": f"{newsout}",
            }
        ],
        max_tokens=3000,
        top_p=1,
        n=1,
        stop=None,
        temperature=0.8,
    )

    # Calculate the total tokens and cost
    generation_tokens = response['usage']['total_tokens']
    summary_tokens = total_token_count
    total_tokens = generation_tokens + total_token_count
    cost = 0.06 * total_tokens / 1000

    # Add tokens and cost to the database
    session = Session()
    token_entry = GptTokenUsage(generation_tokens=generation_tokens,
                                 summary_tokens=summary_tokens,
                                 total_tokens=total_tokens,
                                 cost=cost)
    session.add(token_entry)
    session.commit()

    # Fetch the total tokens and total cost used so far
    total_tokens_so_far = session.query(
        func.sum(GptTokenUsage.total_tokens)).scalar()
    total_cost_so_far = session.query(
        func.sum(GptTokenUsage.cost)).scalar()

    print(f"Tokens used in this generation: {total_tokens}")
    print(f"Cost for this generation: ${cost:.5f}")
    print(f"Total tokens used so far: {total_tokens_so_far}")
    print(f"Total cost so far: ${total_cost_so_far:.5f}")

    result = response.choices[0].message['content'].strip()
    return {"result": result}

    session.close()

    


def process_url(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
    except Exception as e:
        return f"Error: {str(e)}"

    headline = article.title
    body = article.text

    # Trim the body to a certain length, for example 2000 characters
    body = body[:2000]

    content = f"Heading: {headline}\n\nSnippet: {body}\n\n"

    return content


def process_with_gpt(content):
    print("Summarizing the news articles with Summary GPT")
    # Adjust the prompt to include the product_url in the desired place.
    prompt = f"{content}\n\n------End of post. Below are instructions you must follow----------------\n\nYou are Montaigne, a smart, witty, and creative journalist. I am looking for a summary with a heading based on the above post. Channel your inner Kara Swisher, Joanna Stern, Alex Kantrowitz, Tim Urban, Maria Popova, Shane Parrish, Ann Handley, and James Clear to craft a summary that will leave our busy and highly successful entrepreneur readers in awe, making them crave more of your unique news coverage. Remember, your goal is to inform while staying true to the essence of the original content. Combine the fearlessness of Swisher, the relatability of Stern, the analytical prowess of Kantrowitz, and the wit and creativity of the other writers mentioned to create a truly engaging summary. Most importantly, keep the language simple and professional. Go ahead, give us a memorable and very intriguing summary. Don't miss on the details mentioned in the article like people names, their background and include information about the use cases as well. \nThe output should not exceed 150 words."

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1000,
        top_p=1,
        n=1,
        stop=None,
        temperature=0.9,
    )
    result = response.choices[0].text.strip()
    token_counts = response['usage']['total_tokens']
    print(token_counts)
    return result, token_counts



if __name__ == '__main__':
    app.run()


