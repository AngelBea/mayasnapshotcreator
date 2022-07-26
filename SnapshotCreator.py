from datetime import date, datetime
from fileinput import filename
from maya import cmds, OpenMaya as mayaLib, OpenMayaUI as mayaUi
import pymel.core.uitypes as pymui
from pymel import core as pym

import os as system

mainWindow = pym.ui.Window(pym.MelGlobals.get('gMainWindow'))

editableUiObjects = {}
cameraConfig = {}
configOptions = {}
ratioOptions = {}
displayOptions = {}
panelsByCamera = {}

cameras = []
panels = []

windowName = "SnapshotCreator"
windowNameConfig = "ConfigWindow"
windowTitleConfig = "Configure your presets"
windowTitle = "Snapshot Creator by Angel Bea"
placeHolderProjectPath = "Add a folder to save the snapshots"
projectPath = placeHolderProjectPath
initTextLogConsole = "Initializing... Welcome to Snapshot Creator 0.1"

mainWidth = pym.window(mainWindow, query=True, width=True)
mainHeight = pym.window(mainWindow, query=True, height=True)

responsiveSize = 0.50
configResponsiveSize = 0.50
heightResponsive = mainHeight * responsiveSize
widthResponsive = mainWidth * responsiveSize

configHeightResponsive = mainHeight * configResponsiveSize
configWidthResponsive = mainWidth * configResponsiveSize

def start_ui():
    get_cameras_with_panels()
    delete_window(windowNameConfig)
    delete_window(windowName)
    windowLayout = new_window()
    load_options()
    load_config()
    create_elements(windowLayout)
    check_folder_selected()
    config_camera()

    pym.showWindow()


def new_window():
    pym.window(
        windowName, 
        maximizeButton=False, 
        title=windowTitle, 
        sizeable=False, 
        width=widthResponsive, 
        height=heightResponsive
        )
    return pym.formLayout()

def delete_window(window):
    if pym.window(window, exists=True):
        pym.deleteUI(window)

def create_elements(layout):
    #Responsive variables
    widthTextField = widthResponsive * 0.50
    widthButton = widthResponsive * 0.05
    widthLogConsole = widthResponsive * 0.30
    heightLogConsole = heightResponsive * 0.10 
    widthActionsLabel = widthResponsive * 0.10
    heightActionsLabel = heightResponsive * 0.05
    heightActionButtons = heightResponsive * 0.05
    widthActionsButtons = widthResponsive * 0.15
    widthOpenConfigButton = widthResponsive * 0.05
    widthOptionsCamera = widthResponsive * 0.15

    topOffsetFirstRow = 10
    cameraSelectionTopOffset = topOffsetFirstRow + 60
    labelCameraSelectionTopOffset = topOffsetFirstRow + 40

    topOffsetSecondRow = heightLogConsole + topOffsetFirstRow + 30
    topOffsetSecondRowFirstButton = topOffsetSecondRow + heightActionsLabel

    leftOffsetTextField = 20
    leftOffsetButton = widthTextField + leftOffsetTextField + 10
    leftOffsetConsoleLog = leftOffsetButton + widthButton + 100
    leftActionsOffset = leftOffsetConsoleLog + 100
    leftOffsetConfigbutton = leftOffsetTextField + widthOptionsCamera + 10

    #First Row
    pathTextField = pym.textField("PathField", editable=False, text=projectPath, width=widthTextField)
    layout.attachForm(pathTextField, "top", topOffsetFirstRow)
    layout.attachForm(pathTextField, "left", leftOffsetTextField)
    editableUiObjects["pathTextField"] = pathTextField

    logConsole = pym.textScrollList("LogConsole", enable=False, width=widthLogConsole, height=heightLogConsole, selectCommand="deselect_on_select_log()")
    logConsole.append(initTextLogConsole)
    layout.attachForm(logConsole, "top", topOffsetFirstRow)
    layout.attachForm(logConsole, "left", leftOffsetConsoleLog)
    editableUiObjects["logConsole"] = logConsole


    buttonFolder = pym.button(l=u"\U0001F5C1", width=widthButton, command='select_folder()')
    layout.attachForm(buttonFolder, "top", topOffsetFirstRow)
    layout.attachForm(buttonFolder, "left", leftOffsetButton)

    #Camera and Config
    labelSelectCamera = pym.text("Select Camera")
    layout.attachForm(labelSelectCamera, "top", labelCameraSelectionTopOffset)
    layout.attachForm(labelSelectCamera, "left", leftOffsetTextField)

    optionMenu = pym.optionMenu(changeCommand="config_camera()", maxVisibleItems=6, width=widthOptionsCamera)
    editableUiObjects["camera"] = optionMenu

    for cam in cameras:
        pym.menuItem(label=f'{cam}')

    layout.attachForm(optionMenu, "top", cameraSelectionTopOffset)
    layout.attachForm(optionMenu, "left", leftOffsetTextField)

    editor = pym.modelEditor(camera=cameraConfig["camera"], activeView=True, width=600, height=600, displayTextures=True, displayAppearance="smoothShaded")
    editableUiObjects["editor"] = editor
    pym.formLayout(layout, edit=True, attachForm=[(editor, 'top', 500), (editor, 'left', 500)])

    buttonConfig = pym.button(l=u"\u2699", width=widthOpenConfigButton, command="load_config_window()")
    layout.attachForm(buttonConfig, "top", cameraSelectionTopOffset)
    layout.attachForm(buttonConfig, "left", leftOffsetConfigbutton)

    #Second Row
    actionsLabel = pym.text(l='Actions', width=widthActionsLabel, font='boldLabelFont', recomputeSize=True, height=heightActionsLabel)
    layout.attachForm(actionsLabel, "top", topOffsetSecondRow)
    layout.attachForm(actionsLabel, "left", leftActionsOffset)

    buttonSaveSnapshot = pym.button(l=u"\U0001F4F7 Save Snapshot", width=widthActionsButtons, height=heightActionButtons, backgroundColor=(0, 0.355, 0.25), command='save_snapshot()')
    layout.attachForm(buttonSaveSnapshot, "top", topOffsetSecondRowFirstButton)
    layout.attachForm(buttonSaveSnapshot, "left", leftActionsOffset - 25)

def select_folder():
    folderSelected = pym.fileDialog2(cap='Select the snapshot folder', okCaption='Select', fileMode=3, dialogStyle=2)
    global projectPath 
    projectPath = folderSelected[0]
    add_log(f"Folder added: {folderSelected[0]}")
    editableUiObjects["pathTextField"].setText(folderSelected[0])

def add_log(text):
    if editableUiObjects:
        logConsole = editableUiObjects["logConsole"]
        logConsole.append(text)
        logConsole.showIndexedItem(logConsole.getNumberOfItems())
    
def deselect_on_select_log():
    logConsole = editableUiObjects["logConsole"]
    logConsole.deselectAll()

def save_snapshot():
    if check_folder_selected():
        #pym.lookThru(cameraConfig['camera'])

        if '16:9' in cameraConfig['resolution']:
            pym.viewFit(cameraConfig['camera'], f=0.5)
        else:
            pym.viewFit(cameraConfig['camera'])
        fileName = f"{projectPath}/{cameraConfig['camera']}_screenshot_{datetime.today().strftime('%Y-%m-%d_%H.%M.%S')}"
        pym.playblast(
            editorPanelName=editableUiObjects["editor"],
            format='image', 
            filename= fileName,
                        startTime=0,
                        endTime=0,
                        sequenceTime =0,
                        clearCache=0,
                        viewer=0,
                        showOrnaments=0,
                        framePadding=0, percent=100,
                        compression=f"{cameraConfig['file type']}",
                        quality=100,
                        widthHeight=ratioOptions[cameraConfig["resolution"]]
        )

def load_config():
    if not cameraConfig:
        cameraConfig["camera"] = f"{cameras[0]}"
        cameraConfig["lights"] = configOptions["lights"][3];
        cameraConfig["display"] = configOptions["display"][1];
        cameraConfig["transparent"] = True;
        cameraConfig["resolution"] = configOptions["resolution"][2];
        cameraConfig["file type"] = configOptions["file type"][0];
        cameraConfig["fit camera"] = True
        add_log("Config loaded")

def load_options():
    global configOptions
    configOptions["display"] = ["flatShaded", "smoothShaded"]
    configOptions["lights"] = ["all", "default", "active", "flat"]
    configOptions["resolution"] = ['[1:1] - 512', '[16:9] - 480p - ED',
            '[1:1] - 1K', '[16:9] - 720p - HD' , '[16:9] - 1080p - FHD',
            '[1:1] - 2K', '[16:9] - 1440p - QHD', 
            '[1:1] - 4K', '[16:9] - 2160p - UHD']
    configOptions["file type"] = ["png", "jpg"]
    
    ratioOptions['[1:1] - 512'] = (512, 512)
    ratioOptions['[1:1] - 1K'] = (1024, 1024)
    ratioOptions['[1:1] - 2K'] = (2048, 2048)
    ratioOptions['[1:1] - 4K]'] = (4096, 4096)

    ratioOptions['[16:9] - 480p - ED'] = (854, 480)
    ratioOptions['[16:9] - 720p - HD'] = (1280, 720)
    ratioOptions['[16:9] - 1080p - FHD'] = (1920, 1080)
    ratioOptions['[16:9] - 1440p - QHD'] = (2560, 1440)
    ratioOptions['[16:9] - 2160p - UHD'] = (3840, 2160)

def load_config_window():
    delete_window(windowNameConfig)
    widthHeightWindow = 512
    widthOptionsCamera = widthResponsive * 0.30
    configOffsetTop = 25
    configOffsetLeft = 25
    numberOfConfigs = 1

    pym.window(windowNameConfig, title=windowTitleConfig, sizeable=False, width=widthHeightWindow, height=widthHeightWindow)
    layout = pym.formLayout()
    for configKey in configOptions.keys():
        option = pym.optionMenu(label=configKey.capitalize(), changeCommand=f"config_changed('{configKey}')", maxVisibleItems=6, width=widthOptionsCamera)

        layout.attachForm(option, "top", configOffsetTop * numberOfConfigs)
        layout.attachForm(option, "left", configOffsetLeft)
        editableUiObjects[configKey] = option

        numberOfConfigs += 1
        for value in configOptions[configKey]:
            pym.menuItem(label=value)

        option.setSelect(configOptions[configKey].index(cameraConfig[configKey]) + 1)

    
    pym.showWindow()

def config_changed(config):
    item = editableUiObjects[config].getValue()
    cameraConfig[config] = item    
    return item

def config_camera():
    camera = config_changed('camera')
    print(editableUiObjects["editor"])
    
    pym.modelEditor(editableUiObjects["editor"], edit=True, camera=camera, activeView=True)
    #pym.lookThru(camera)
    print(editableUiObjects["editor"].getCamera())
    print(editableUiObjects["editor"].getActiveView())
    
    

def check_folder_selected():
    if projectPath == placeHolderProjectPath:
        add_log('[WARNING] Add a folder to save your snapshots')
        return False
    else:
        return True

def get_cameras_with_panels():
    global cameras, panels
    panels = pym.getPanel(type='modelPanel')
    cameras = []

    for panel in panels:
        print(panel)
        try:
            modelPanelCamera = pym.modelPanel(panel, query=True, camera=True)
            print(modelPanelCamera)
            cameras.append(modelPanelCamera)
            panelsByCamera[modelPanelCamera] = panel
        except:
            print('No camera in this panel')
            continue

start_ui()