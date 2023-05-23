import gradio as gr
import os
import subprocess
import sys
import time

# Use current time as miliseconds to give each result a unique name
def current_milli_time():
    return round(time.time() * 1000)


# Define paths
facedancer_path = os.path.abspath("./FaceDancer")
facedancer_path = facedancer_path.replace(os.sep, '/')
facedancer_model_path = os.path.abspath("./FaceDancer/model_zoo/FaceDancer_config_c_HQ.h5")
facedancer_model_path = facedancer_model_path.replace(os.sep, '/')

# This is where magic starts
def swap_faces(inputImg, targetImg, targetVid, inputType):
    resultFileName = "results/{}".format(current_milli_time())
    outputFile = os.path.join(facedancer_path, resultFileName)
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
        for line in process.stdout:
            print(line)
        # Wait for the process to finish
        process.wait()
        if inputType == "Image":
            return [outputFile + ".png", None]
        else:
            return [None, outputFile + ".mp4"]
    except subprocess.CalledProcessError as e:
        print(e.output)
        return [None, None]


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
        saveDirectoryButton = gr.Button(value="📂 Open save directory")
        saveDirectoryButton.click(fn=open_save_dir)
        actionButton.click(fn=swap_faces, inputs=[imageInput, targetImageInput, targetVideoInput, inputType], outputs=[swappedImageOutput,swappedVideoOutput])
if __name__ == "__main__":
    demo.launch()   
