# FaceDancer WebUI
This project is aimed to create an easy to use user interface for FaceDancer, just drag and drop your images/videos, it'll handle the rest.

## Screenshots
![Screenshot of the app](screenshot.jpg)

## Requirements
- FaceDancer must be downloaded, follow the original installation guide [here](https://github.com/felixrosberg/FaceDancer/tree/main#installation)
- Any facedancer model you want


## Installation
- First install gradio
```shell
pip install gradio
```
- Run the app
```shell
python app.py
# Run with live reload using the following command if you want to edit the code
gradio app.py
```

## Todos
- [ ] Move gif input to image box (Looks like it can't be done because of gradio inputting the selected gif as .png file)
- [ ] Add webcam input
- [x] Add model selector
- [x] Add ~~live~~ console output to UI
- [ ] Add options to save as png, jpg, mp4 etc.
- [ ] Prevent UI elements from getting to tall and crossing 100% height