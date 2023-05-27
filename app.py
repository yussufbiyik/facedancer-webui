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

def change_model(dropdown):
    global selected_model
    selected_model = dropdown
    print("Changed model to " + selected_model)

# This is where magic starts
def swap_faces(inputImg, targetImg, targetVid, inputType):
    facedancer_model_path = os.path.join(facedancer_model_zoo, selected_model).replace(os.sep, '/')
    resultFileName = "results/{}".format(current_milli_time())
    outputFile = os.path.join(facedancer_path, resultFileName).replace(os.sep, '/')
    # Use related script based on the input type 
    # and save as .png if it's image
    # if not save as .mp4 
    mainTarget=targetVid
    if inputType=="Image":
        mainTarget = targetImg
        cmd = '''cd {} && conda activate facedancer && python test_image_swap_multi.py --facedancer_path "{}" --swap_source "{}" --img_path "{}" --img_output "{}.png"'''.format(facedancer_path, facedancer_model_path, inputImg, mainTarget, outputFile)
    else:
        cmd = '''cd {} && conda activate facedancer && python test_video_swap_multi.py --facedancer_path "{}" --swap_source "{}" --vid_path "{}" --vid_output "{}.mp4"'''.format(facedancer_path, facedancer_model_path, inputImg, mainTarget, outputFile)
    try:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        consoleLog = ""
        for line in process.stdout:
            print(line)
            consoleLog += line
        # Wait for the process to finish
        process.wait()
        if inputType == "Image":
            return [outputFile + ".png", None, consoleLog]
        else:
            return [None, outputFile + ".mp4", consoleLog]
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

# Create the UI
with gr.Blocks() as demo:
    demo.title = "FaceDancer WebUI"
    gr.Markdown("Put your swap source and target video/image to related inputs then click the run button to get the output.")
    with gr.Row().style(equal_height=True):
        imageInput = gr.Image(label="Swap Source", type="filepath")
        targetImageInput = gr.Image(label="Swap Target Image", type="filepath")
        targetVideoInput = gr.Video(label="Swap Target Video / Gif")
    with gr.Row().style(equal_height=True):
        swappedImageOutput = gr.Image(label="Swaped Image Result")
        swappedVideoOutput = gr.Video(label="Swapped Video Result")
    with gr.Row().style(equal_height=True):
        with gr.Column():
            inputType = gr.Radio(interactive=True,label="Target is:",show_label=True, value="Image", choices=["Image", "Video / Gif"])
            actionButton = gr.Button(value="🎭 Swap Faces",variant="primary")
        with gr.Column():
            selectModelDropdown = gr.Dropdown(choices=model_zoo_models, label="💾 Select Model", value=selected_model, interactive=True, allow_custom_value=False)
            saveDirectoryButton = gr.Button(value="📂 Open save directory")
        saveDirectoryButton.click(fn=open_save_dir)
        selectModelDropdown.change(fn=change_model, inputs=[selectModelDropdown])
    consoleOutputPanel = gr.Code(label="Console Output", value="# Starting point\n", interactive=False, language="shell")
    actionButton.click(fn=swap_faces, inputs=[imageInput, targetImageInput, targetVideoInput, inputType], outputs=[swappedImageOutput,swappedVideoOutput, consoleOutputPanel])
if __name__ == "__main__":
    demo.launch()   
