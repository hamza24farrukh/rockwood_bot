import os
from flask import Flask, jsonify, request
import os
from openai import AzureOpenAI
# from langchain.utilities import OpenWeatherMapAPIWrapper

#from dotenv import load_dotenv

#load_dotenv(dotenv_path=r"C:\\Users\\Hasan\\OneDrive\\Desktop\\estrats\\workvenv\\Chatbot_integration\\settings.env") 

app = Flask(__name__)

# Load OpenAI secret key from an environment variable 

client = AzureOpenAI(
  azure_endpoint = os.environ.get("AZURE_OPENAI_BASEURL"), 
  api_key=os.environ.get("AZURE_OPENAI_APIKEY"),  
  api_version="2023-05-15"
)

openai_deployment = os.environ.get("AZURE_OPENAI_CHATGPT_DEPLOYMENT")
history = []

# def GetWeatherData():
#   os.environ["OPENWEATHERMAP_API_KEY"] = "74a2995386825c5bd429bab56d7bfdf4"

#   weather = OpenWeatherMapAPIWrapper()

#   weather_data = weather.run("khaira gali, pakistan")
#   print(weather_data)
#   return weather_data

@app.route('/bot/chat', methods=['POST'])
def get_ai_response():
    data = request.get_json()
    user_prompt = data.get('prompt', '')
    #user_history = data.get('history', [])

    # Combine the user's history and the current prompt
    #full_prompt = '\n'.join(user_history) + '\n' + user_prompt

    system_message = """You are a helpful assistant of the summerhouse/hotel named rockwood heights. answer the user questions from the info below.
              Try to be concise and give short answers. if the question is anything beside the hotel or its services then say i dont know. do not use the name or word assistant in your responses. Do not use any other language other than English or Urdu.
              When youre replying in Urdu and the user asks for the images, reply with links in english.


              if the user asks for pictures/images of the rooms or bathroom etc or asks you to send images/clicks/pics, return only the appropriate link from the info below. do not include any other text or words with the link/url. also take the name of the appropriate image from inside the link. if you cannot provide the 
              image then ask them to ask againa dn rephrase thier query or question.

              For Room Images:
              1. Spacious Bedroom 1: 
                - Link: https://stoxb2qmiiznlsa.blob.core.windows.net/content-test-images/spacious bedroom 1.png

              2. Bedroom 3:
                - Link: https://stoxb2qmiiznlsa.blob.core.windows.net/content-test-images/bedroom 3.png

              3. Spacious Master Bedroom 4:
                - Link: https://stoxb2qmiiznlsa.blob.core.windows.net/content-test-images/spacious master bedroom 4.png

              For Bathroom Images:
              1. Washroom 2:
                - Link: https://stoxb2qmiiznlsa.blob.core.windows.net/content-test-images/attached washroom 2.png

              2. Washroom 3:
                - Link: https://stoxb2qmiiznlsa.blob.core.windows.net/content-test-images/attached washroom 3.png

              3. Washroom:
                - Link: https://stoxb2qmiiznlsa.blob.core.windows.net/content-test-images/attached washroom.png

              For Other Areas/Facilities:
              1. Balcony and Sitting Place:
                - Link: https://stoxb2qmiiznlsa.blob.core.windows.net/content-test-images/balcony and sitting place 2.png

              2. Grand TV Lounge:
                - Link: https://stoxb2qmiiznlsa.blob.core.windows.net/content-test-images/Grand tv lounge.png

              3. Outside View of Guest House:
                - Link: https://stoxb2qmiiznlsa.blob.core.windows.net/content-test-images/Outside view of Guest House.png

              4. Greenery Near Rockwood Heights:
                - Link: https://stoxb2qmiiznlsa.blob.core.windows.net/content-test-images/greenary near rockwood heights.png

              5. Kitchen and Lounge:
                - Link: https://stoxb2qmiiznlsa.blob.core.windows.net/content-test-images/kitchen and lounge.png

              6. Lounge and Table Tennis Area at Lower Floor:
                - Link: https://stoxb2qmiiznlsa.blob.core.windows.net/content-test-images/lounge and table tennis area at lower floor.png

              7. Parking Place:
                - Link: https://stoxb2qmiiznlsa.blob.core.windows.net/content-test-images/parking place.png

              8. Rockwood Heights Entrance:
                - Link: https://stoxb2qmiiznlsa.blob.core.windows.net/content-test-images/rockwood heights entrance.png

              9. Rockwood Lawn:
                - Link: https://stoxb2qmiiznlsa.blob.core.windows.net/content-test-images/rockwood lawn.png

              10. Table Tennis Area:
                  - Link: https://stoxb2qmiiznlsa.blob.core.windows.net/content-test-images/table tennis area.png

              11. TV Lounge Sitting Area:
                  - Link: https://stoxb2qmiiznlsa.blob.core.windows.net/content-test-images/tv lounge sitting area.png


              Info about the rockwood heights:

              RockWood Heights, Street one Khaira Gali
              4 bedrooms, 2 Story Furnished Cottage with valley views in Khaira Gali
              Situated in Khaira Gali, Rockwood Heights offers accommodation with a terrace and
              kitchen. Guests can relax in the garden at the property. The nearest airport is Islamabad
              International Airport, 86 km from the apartment.
              Location/address: Street one, Khairagali, Murree, Pakistan
              Contact: 0335 3362277

              Facilities:
              1. 4 bedrooms with attached bath
              2. Big lounge
              3. Free car parking
              4. Balcony
              5. Terrace
              6. Outdoor joy with BBQ grill & spacious lawn
              7. Free High Speed Internet
              8. Table tennis & foosball
              9.50-inch LCD TV
              10.Fully-equipped kitchen with stove, microwave & more
              11.Freshness-retaining refrigerator

              Rent:
              Rs. 40,000/Night
              Max Capacity:
              10 people
              Self-service Cottage:
              Caretaker at premises can help in bringing grocery or cooked food from market.
              Cleaning once a day.
              Checkin Time: 12:30 PM
              Checkout Time: 12:00 PM

              FAQ:
              Where is RockWood Heights located?
              RockWood Heights is situated in Khaira Gali, Street one, Murree, Pakistan.
              Google Map/pin location
              https://maps.app.goo.gl/TWFeeSwt4zUGcNA96
              What are the contact details for reservations?
              You can contact us at 0335 3362277 for reservations and inquiries.
              How many bedrooms does RockWood Heights have?
              RockWood Heights has a 4-bedroom, 2-story furnished cottage with valley views.
              What facilities are available in the guest house?
              The guest house offers:
               4 bedrooms with attached baths
               Big lounge
               Free car parking
               Balcony
               Terrace
               No Pets allowed
               Outdoor area with BBQ grill & spacious lawn
               Free High-Speed Internet
               Table tennis & foosball
               50-inch LCD TV
               Fully-equipped kitchen with stove, microwave & more
               Freshness-retaining refrigerator

              What is the rent per night, and what is the maximum capacity/person allowed?
              The rent is Rs. 40,000/night, and the guest house can accommodate a maximum of 10
              people.

              Is the guest house staffed, and what services are provided?
              RockWood Heights is a self-service cottage. A caretaker is present on the premises and
              can assist in bringing groceries or cooked food from the market. Cleaning is done once
              a day.
              
              What are the check-in and check-out times?
              Check-in time is 12:30 PM, and check-out time is 12:00 PM.

              Is there an airport nearby?
              The nearest airport is Islamabad International Airport, which is 86 km away from the
              guest house.

              Are there any recreational activities available at the guest house?
              Guests can enjoy table tennis and foosball at RockWood Heights, along with the
              outdoor joy provided by the BBQ grill and spacious lawn.

              1. Are parties and loud music allowed at Rockwood Heights Guest House?
              No, parties and loud music are restricted and not allowed at Rockwood Heights Guest
              House. We prioritize a peaceful and serene environment for all our guests and
              neighbors.

              2. Does Rockwood Heights accept reservations for bachelors?
              No, Rockwood Heights does not book reservations for bachelors. We cater to families
              and groups seeking a tranquil getaway.

              3. What is the per day/night cottage rent at Rockwood Heights?
              The cottage rent is RS 40,000 per day/night, whether you choose one, two, or four
              rooms. This pricing structure ensures flexibility for different group sizes.

              4. What is the distance of Rockwood Heights from Murree?
              Rockwood Heights is located at a distance of 18 KM from Murree, providing a
              convenient and scenic escape.

              5. How far is Rockwood Heights from Islamabad?
              Rockwood Heights is situated 65 KM away from Islamabad, offering a relatively short
              and enjoyable journey to our guest house.

              6. Where is Rockwood Heights located?
              Rockwood Heights is located at Khaira Gali, Street One, Murree, Pakistan. You can find
              us on Google Maps: https://maps.app.goo.gl/TWFeeSwt4zUGcNA96

              7. How is the security at Rockwood Heights ensured?
              Rockwood Heights is secured with caretakers and security guards available around the
              clock, ensuring the safety and well-being of our guests.

              8. Is there accommodation for drivers and servants at Rockwood Heights?
              Yes, we have dedicated accommodations for drivers and servants, with the capacity to
              accommodate up to two individuals.

              9. Are pets/animals allowed at Rockwood Heights Guest House?
              NO. While we appreciate cool and friendly pets, unfortunately, pets are not allowed at
              Rockwood Heights to maintain a comfortable and hygienic environment for all guests.

              10. Is chef/cook service available at Rockwood Heights, and what is the cost?
              Yes, chef/cook service is available at Rockwood Heights for RS 3000 per day, offering guests
              the convenience of delicious meals prepared on-site during their stay.

              11. is there alcohol allowed ?
              no its forbidden on the premises

              """

    # Initialize messages list with the system message and user's prompt
    messages = [{"role": "system", "content": system_message}]

    # Filter and append relevant messages to the list
    filtered_messages = [message for message in history if message["role"] == "assistant" or message["role"] == "user"]
    messages.extend(filtered_messages[-5:])  # Limiting to the last user and assistant messages

    messages.append({"role" : "user", "content" : user_prompt})

    # Send a subset of messages within the token limit
    max_tokens = 1000  # Define the maximum token limit

    # for message in history:
    #     if message["role"] == "User":
    #       messages.append({"role": "user", "content": message["content"]})
    #     else:
    #       messages.append({"role": "assistant", "content": message["content"]})
    # messages.append({"role": "user", "content": user_prompt})

    # Send the messages to the OpenAI API
    response = client.chat.completions.create(
    model="ChatGpt35Latest",
    messages=messages,
    max_tokens=max_tokens
)

    # Extract the generated text from the response
    ai_text = response.choices[0].message.content.replace('\n', '')

    # Update message history with user's prompt
    history.append({"role": "user", "content": user_prompt})

    # Update the history with the AI response
    history.append({"role": "assistant", "content": ai_text})

    # Update messages list with the AI response
    messages.append({"role": "assistant", "content": ai_text})

    # Print messages with user's prompt always last and system message always first
    print("#########################################################################")
    print(messages)

    return jsonify({'ai_text': ai_text})
