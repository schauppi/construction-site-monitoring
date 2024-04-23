import requests

def test_start_capture():
    url = 'http://localhost:5000/start'
    response = requests.post(url)
    print(f"Start Capture Response: {response.status_code}, {response.json()}")
    assert response.status_code == 200
    assert response.json()['status'] == 'Started capturing images.'

def test_stop_capture():
    url = 'http://localhost:5000/stop'
    response = requests.post(url)
    print(f"Stop Capture Response: {response.status_code}, {response.json()}")
    assert response.status_code == 200
    assert response.json()['status'] == 'Stopped capturing images.'

def test_status():
    url = 'http://localhost:5000/status'
    response = requests.get(url)
    print(f"Status Response: {response.status_code}, {response.json()}")
    assert response.status_code == 200
    assert response.json()['status'] in ['Capturing', 'Not Capturing']

def test_set_interval():
    url = 'http://localhost:5000/set_interval'
    new_interval = 10  
    response = requests.post(url, json={'interval': new_interval})
    print(f"Set Interval Response: {response.status_code}, {response.json()}")
    assert response.status_code == 200
    assert response.json()['status'] == f'Save interval updated to {new_interval} seconds.'

if __name__ == "__main__":
    test_start_capture()
    #test_status()  # Assuming the capture has started, should return "Capturing"
    #test_set_interval()
    #test_stop_capture()
    #test_status()  # Assuming the capture has stopped, should return "Not Capturing"
