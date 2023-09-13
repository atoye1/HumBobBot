import requests
source_url = "http://130.162.153.197:8000/images/HumBobBot.png"


def upload_image_to_server(source_url, yymmdd, location):
    response = requests.get(source_url)

    if response.status_code != 200:
        print("Failed to retrieve the file.")
        exit()

    image_content = response.content
    post_url = "http://130.162.153.197:8000/upload_diet/"

    # Data to send
    data = {
        "yymmdd": yymmdd,  # Replace with your desired datetime
        "location": location  # Replace with your desired location
    }

    # Image to send
    files = {
        "filename": "test_filename.jpg",
        "file": image_content,
        "size": len(image_content),
        "headers": ""
    }

    post_response = requests.post(post_url, data=data, files=files)
    print(post_response)


if __name__ == "__main__":
    upload_image_to_server(source_url, 112233, '당고개')
