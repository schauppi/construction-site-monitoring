import requests
import cv2

def test_object_detection_api(url, image_path):
    """Send an image to the object detection API and print the response.

    Args:
        url (str): The URL of the object detection API endpoint.
        image_path (str): The path to the image file to upload.
    """
    # Open the image file in binary mode
    with open(image_path, 'rb') as image_file:
        # Prepare the request payload with the image data
        files = {'image': image_file}
        # Send the POST request
        response = requests.post(url, files=files)

    # Check the response status
    if response.status_code == 200:
        print("Response from server: ", response.json())
        return response
    else:
        print("Failed to get a valid response, status code:", response.status_code)
        print("Response text:", response.text)

def plot_bounding_boxes(image_path, boxes, output_path, input_size=(640, 640)):
    """
    Draw bounding boxes on an image and save it.

    Args:
        image_path (str): Path to the original image.
        boxes (list of lists): List of bounding box coordinates [x1, y1, x2, y2].
        output_path (str): Path to save the image with bounding boxes.
        input_size (tuple): Size (width, height) of the image input to the model.
    """
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print("Failed to load image at", image_path)
        return
    
    # Get the original image dimensions
    orig_h, orig_w = image.shape[:2]
    
    # Calculate scale factors
    scale_w, scale_h = orig_w / input_size[0], orig_h / input_size[1]
    
    # Loop through the boxes and draw them on the image
    for box in boxes:
        x1, y1, x2, y2 = box  # Extract coordinates
        # Scale box back to original image size
        x1 = int(x1 * scale_w)
        y1 = int(y1 * scale_h)
        x2 = int(x2 * scale_w)
        y2 = int(y2 * scale_h)
        # Draw rectangle with green line
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Save the modified image
    cv2.imwrite(output_path, image)
    print(f"Saved annotated image at {output_path}")


if __name__ == '__main__':
    # URL of the Flask API endpoint
    api_url = "http://127.0.0.1:5000/detect"
    # Path to the image you want to send for object detection
    test_image_path = "/home/xavier/Documents/construction-site-monitoring/src/detection/image.png"
    out_path = "/home/xavier/Documents/construction-site-monitoring/src/detection/image_2.png"
    response = test_object_detection_api(api_url, test_image_path)
    boxes = response.json()['result_boxes']
    plot_bounding_boxes(test_image_path, boxes, out_path)
