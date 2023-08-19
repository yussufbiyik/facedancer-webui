import gradio as gr
import os
import subprocess
import sys
import time

# Use current time as miliseconds to give each result a unique name
def current_milli_time():
    return round(time.time() * 1000)


# Define paths
selected_model = "FaceDancer_config_c_HQ.h5"
facedancer_path = os.path.abspath("./FaceDancer").replace(os.sep, '/')
facedancer_model_zoo = os.path.join(facedancer_path, "model_zoo").replace(os.sep, '/')
model_zoo_models = list(filter(lambda file: file.endswith(".h5"), os.listdir(facedancer_model_zoo)))

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

# This is where magic starts
def swap_faces(inputImg, targetImg, targetVid, inputType):
    facedancer_model_path = os.path.join(facedancer_model_zoo, selected_model).replace(os.sep, '/')
    resultFileName = f"results/{int(time.time())}"
    outputFile = os.path.join(facedancer_path, resultFileName).replace(os.sep, '/')
    # Determine main target and output extension based on input type
    mainTarget = targetImg if inputType == "Image" else targetVid
    commandSpecific = "img" if inputType == "Image" else "vid"
    swap_output_extension = output_extension if inputType == "Image" else output_extension_video
    # Choose the appropriate script name based on input type
    script_name = "test_image_swap_multi.py" if inputType == "Image" else "test_video_swap_multi.py"
    # Construct the command
    cmd = f'''cd {facedancer_path} && conda activate facedancer && python {script_name} --facedancer_path "{facedancer_model_path}" --swap_source "{inputImg}" --{commandSpecific}_path "{mainTarget}" --{commandSpecific}_output "{outputFile}.{swap_output_extension}"'''
    try:
        # Execute the command and capture console output
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        consoleLog = process.communicate()[0]
        print(consoleLog)
        # Determine return values based on input type
        if inputType == "Image":
            return [f"{outputFile}.{swap_output_extension}", None, consoleLog]
        else:
            return [None, f"{outputFile}.{output_extension_video}", consoleLog]
    except subprocess.CalledProcessError as e:
        print(e.output)
        return [None, None, consoleLog]

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
            imageInput = gr.Image(label="Swap Source", type="filepath")
            with gr.Column():
                targetImageInput = gr.Image(label="Swap Target Image", type="filepath")
                webcamToggleButton = gr.Button(value="Toggle Webcam 📷", variant="primary")
            targetVideoInput = gr.Video(label="Swap Target Video / Gif")
        with gr.Row().style(equal_height=True):
            swappedImageOutput = gr.Image(label="Swaped Image Result")
            swappedVideoOutput = gr.Video(label="Swapped Video Result")
        with gr.Row().style(equal_height=True):
            inputType = gr.Radio(interactive=True,label="Target is:",show_label=True, value="Image", choices=["Image", "Video / Gif"])
            with gr.Row().style(equal_height=True):
                actionButton = gr.Button(value="🎭 Swap Faces",variant="primary")
                saveDirectoryButton = gr.Button(value="📂 Open save directory")
                saveDirectoryButton.click(fn=open_save_dir)
        with gr.Row().style(equal_height=True):
            webUILogs = gr.Code(label="WebUI Logs", value="# Starting point\n", interactive=False, language="shell")
            consoleOutputPanel = gr.Code(label="FaceDancer Output", value="# Starting point\n", interactive=False, language="shell")
        actionButton.click(fn=swap_faces, inputs=[imageInput, targetImageInput, targetVideoInput, inputType], outputs=[swappedImageOutput,swappedVideoOutput, consoleOutputPanel])
        webcamToggleButton.click(fn=toggle_webcam, outputs=[targetImageInput, consoleOutputPanel])
    with gr.Tab("Settings"):
        selectModelDropdown = gr.Dropdown(choices=model_zoo_models, label="💾 Select Model", value=selected_model, interactive=True, allow_custom_value=False)
        selectVideoOutputExtensionDropdown = gr.Dropdown(choices=["mp4", "webm"], label="📹 Select Video Output", value="mp4", interactive=True, allow_custom_value=True)
        selectImageOutputExtensionDropdown = gr.Dropdown(choices=["png", "jpg"], label="📸 Select Image Output", value="png", interactive=True, allow_custom_value=True)
        selectVideoOutputExtensionDropdown.change(fn=change_video_output_extension, inputs=[selectVideoOutputExtensionDropdown], outputs=[webUILogs])
        selectImageOutputExtensionDropdown.change(fn=change_image_output_extension, inputs=[selectImageOutputExtensionDropdown], outputs=[webUILogs])
        selectModelDropdown.change(fn=change_model, inputs=[selectModelDropdown], outputs=[webUILogs])
if __name__ == "__main__":
    demo.launch(server_port=7960)   
