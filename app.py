import gradio as gr
import os
import subprocess
import sys
import time

sys.path.insert(1, './FaceDancer')
import logging

import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow_addons.layers import InstanceNormalization

from networks.layers import AdaIN, AdaptiveAttention
from retinaface.models import *
from utils.swap_func import run_inference
from utils.swap_func import video_swap

logging.getLogger().setLevel(logging.ERROR)

# Use current time as miliseconds to give each result a unique name
def current_milli_time():
    return round(time.time() * 1000)


# Define paths
selected_model = "FaceDancer_config_c_HQ.h5"
facedancer_path = os.path.abspath("./FaceDancer").replace(os.sep, '/')
facedancer_model_zoo = os.path.join(facedancer_path, "model_zoo").replace(os.sep, '/')
model_zoo_models = list(filter(lambda file: file.endswith(".h5"), os.listdir(facedancer_model_zoo)))
retina_path = "./FaceDancer/retinaface/RetinaFace-Res50.h5"
arcface_path = "./FaceDancer/arcface_model/ArcFace-Res50.h5"

# Define defaults
output_extension = "png"
output_extension_video = "mp4"
image_input_source = "upload"

def change_model(dropdown):
    global selected_model
    selected_model = dropdown
    infoMessage = "Changed model to " + selected_model
    print(infoMessage)
    return infoMessage

def change_video_output_extension(extension):
    global output_extension_video
    output_extension_video = extension
    infoMessage = "Changed video output extension to " + extension
    print(infoMessage)
    return infoMessage


def change_image_output_extension(extension):
    global output_extension
    output_extension = extension
    infoMessage = "Changed image output extension to " + extension
    print(infoMessage)
    return infoMessage


if __name__ == '__main__':
    if len(tf.config.list_physical_devices('GPU')) != 0:
        gpus = tf.config.experimental.list_physical_devices('GPU')
        tf.config.set_visible_devices(gpus["0"], 'GPU')

    print('\nInitializing FaceDancer...')
    RetinaFace = load_model(retina_path, compile=False,
                            custom_objects={"FPN": FPN,
                                            "SSH": SSH,
                                            "BboxHead": BboxHead,
                                            "LandmarkHead": LandmarkHead,
                                            "ClassHead": ClassHead})
    ArcFace = load_model(arcface_path, compile=False)
    facedancer_model_path = os.path.join(facedancer_model_zoo, selected_model).replace(os.sep, '/')
    G = load_model(facedancer_model_path, compile=False,
                custom_objects={"AdaIN": AdaIN,
                                "AdaptiveAttention": AdaptiveAttention,
                                "InstanceNormalization": InstanceNormalization})
    G.summary()

def handle_facedancer(mode, params):
    resultPath = ""
    if mode == "Image":
        print('\nProcessing: {}'.format(params.img_path))
        run_inference(params, params.swap_source, params.img_path,
                RetinaFace, ArcFace, G, params.img_output)
        print('\nDone! {}'.format(params.img_output))
        resultPath = params.img_output
    else:
        print('\nProcessing: {}'.format(params.vid_path))
        video_swap(params, params.swap_source, params.vid_path, RetinaFace, ArcFace, G, params.vid_output)
        resultPath = params.vid_output
    return resultPath
# This is where magic starts
def swap_faces(inputImg, targetImg, targetVid, inputType):
    facedancer_model_path = os.path.join(facedancer_model_zoo, selected_model).replace(os.sep, '/')
    resultFileName = f"results/{int(time.time())}"
    outputFile = os.path.join(facedancer_path, resultFileName).replace(os.sep, '/')
    swap_output_extension = output_extension if inputType == "Image" else output_extension_video
    class FacedancerOptions:
        device_id = "0"
        retina_path = "./FaceDancer/retinaface/RetinaFace-Res50.h5"
        arcface_path = "./FaceDancer/arcface_model/ArcFace-Res50.h5"
        facedancer_path = facedancer_model_path
        swap_source = inputImg
        vid_path = targetVid
        img_path = targetImg
        vid_output = f"{outputFile}.{swap_output_extension}"
        img_output = f"{outputFile}.{swap_output_extension}"
        align_source = True
    resultPath = handle_facedancer(inputType, FacedancerOptions())
    if inputType == "Image":
        return [resultPath, None, "Finished"]
    else:
        return [None, resultPath, "Finished"]

# Opens the save directory in dedicated expolorer of each os
def open_save_dir():
    if sys.platform.startswith("win"):
        os.startfile(os.path.join(facedancer_path, "results"))
    elif sys.platform.startswith("darwin"):
        subprocess.run(["open", os.path.join(facedancer_path, "results")])
    elif sys.platform.startswith("linux"):
        subprocess.run(["xdg-open", os.path.join(facedancer_path, "results")])
    else:
        print("Unsupported operating system.")

def toggle_webcam():
    global image_input_source
    image_input_source = "webcam" if image_input_source == "upload" else "upload"
    return [{"source": image_input_source, "__type__": "update"}, {"value":f"Source changed to {image_input_source.capitalize()}", "__type__": "update"}]

# Create the UI
with gr.Blocks() as demo:
    demo.title = "FaceDancer WebUI"
    with gr.Tab("FaceDancer"):
        gr.Markdown("Put your swap source and target video/image to related inputs then click the run button to get the output.")
        with gr.Row().style(equal_height=True):
            with gr.Column():
                imageInput = gr.Image(label="Swap Source", type="filepath")
                sourceWebcamToggleButton = gr.Button(value="Toggle Webcam")
            with gr.Column():
                targetImageInput = gr.Image(label="Swap Target Image", type="filepath")
                targetWebcamToggleButton = gr.Button(value="Toggle Webcam")
            with gr.Column():
                targetVideoInput = gr.Video(label="Swap Target Video / Gif")   
                videoWebcamToggleButton = gr.Button(value="Toggle Webcam") 
        with gr.Row().style(equal_height=True):
            swappedImageOutput = gr.Image(label="Swaped Image Result")
            swappedVideoOutput = gr.Video(label="Swapped Video Result")
        with gr.Row().style(equal_height=True):
            inputType = gr.Radio(interactive=True,label="Target is:",show_label=True, value="Image", choices=["Image", "Video / Gif"])
            with gr.Row().style(equal_height=True):
                actionButton = gr.Button(value="🎭 Swap Faces",variant="primary")
                saveDirectoryButton = gr.Button(value="📂 Open save directory")
                saveDirectoryButton.click(fn=open_save_dir)
        with gr.Accordion(label="Show Logs", open=False):
            with gr.Row().style(equal_height=True):
                webUILogs = gr.Code(label="WebUI Logs", value="# Starting point\n", interactive=False, language="shell")
                consoleOutputPanel = gr.Code(label="FaceDancer Output", value="# Starting point\n", interactive=False, language="shell")
        actionButton.click(fn=swap_faces, inputs=[imageInput, targetImageInput, targetVideoInput, inputType], outputs=[swappedImageOutput,swappedVideoOutput, consoleOutputPanel])
        sourceWebcamToggleButton.click(fn=toggle_webcam, outputs=[imageInput, consoleOutputPanel])
        targetWebcamToggleButton.click(fn=toggle_webcam, outputs=[targetImageInput, consoleOutputPanel])
        videoWebcamToggleButton.click(fn=toggle_webcam, outputs=[targetVideoInput, consoleOutputPanel])
    with gr.Tab("Settings"):
        selectModelDropdown = gr.Dropdown(choices=model_zoo_models, label="💾 Select Model", value=selected_model, interactive=True, allow_custom_value=False)
        selectVideoOutputExtensionDropdown = gr.Dropdown(choices=["mp4", "webm"], label="📹 Select Video Output", value="mp4", interactive=True, allow_custom_value=True)
        selectImageOutputExtensionDropdown = gr.Dropdown(choices=["png", "jpg"], label="📸 Select Image Output", value="png", interactive=True, allow_custom_value=True)
        selectVideoOutputExtensionDropdown.change(fn=change_video_output_extension, inputs=[selectVideoOutputExtensionDropdown], outputs=[webUILogs])
        selectImageOutputExtensionDropdown.change(fn=change_image_output_extension, inputs=[selectImageOutputExtensionDropdown], outputs=[webUILogs])
        selectModelDropdown.change(fn=change_model, inputs=[selectModelDropdown], outputs=[webUILogs])
if __name__ == "__main__":
    demo.launch(server_port=7960)   
