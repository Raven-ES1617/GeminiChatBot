import os
from openai import OpenAI

BASE_URL = "https://openrouter.ai/api/v1"
API_KEY = os.environ['openrouter_api_key']

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,  # Replace with your actual OpenRouter API key
)


def get_openrouter_response(query, image_url=None):
    """
    Sends a query to the OpenRouter API and returns the response.

    :param query: The text query from the user.
    :param image_url: Optional. The URL of an image to include in the query.
    :return: The response content from the API.
    """
    # Prepare the messages list
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": query}
            ]
        }
    ]

    # Add image URL to the content if provided
    if image_url:
        messages[0]["content"].append({
            "type": "image_url",
            "image_url": {"url": image_url}
        })

    # Send the request to the OpenRouter API
    completion = client.chat.completions.create(
        # extra_headers={
        #     "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional. Site URL for rankings on openrouter.ai.
        #     "X-Title": "<YOUR_SITE_NAME>",  # Optional. Site title for rankings on openrouter.ai.
        # },
        extra_body={},
        model="google/gemini-2.0-flash-lite-preview-02-05:free",
        messages=messages
    )

    return completion.choices[0].message.content

#
# # Example usage
# if __name__ == "__main__":
#     # Get user input
#     user_query = input("Enter your query: ")
#     user_image_url = input("Enter an image URL (or press Enter to skip): ")
#
#     # Call the function and get the response
#     response = get_openrouter_response(user_query, user_image_url if user_image_url else None)
#
#     # Print the response
#     print("Response from OpenRouter:")
#     print(response)
