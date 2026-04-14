spng-tools
==========

Tools for handling the spng image data format used in the E07 emulsion full scanning.

## spng-server.py

A lightweight web-based browser for E07 emulsion data. View images directly from `.spng` files without extracting them to disk.

### Usage

1. Start the Server (KEKCC Side)

Run the script on KEKCC. Specify the root directory containing your data.

``` bash
python spng-server.py /path/to/your/data/root/
```

The server will start on http://0.0.0.0:8000.

2. Set up SSH Tunnel (Local PC Side)

Open a new terminal on your local machine and create a tunnel to forward the port:

``` bash
ssh -L 8000:localhost:8000 your_username@login.kekcc.jp
```

3. Access via Browser

Open your web browser and go to:
http://localhost:8000

![client.png](fig/web-client.png)

### Controls

- Sidebar: Click Directories to navigate; click JSON files to load image stacks.
- Mouse Wheel: Change Z-slice (Index).
- Arrow Keys: Left/Right to change Z-slice.
- View Mode Button: Toggle between scaling the image to fit the window or showing original resolution.
- Projection Button: Calculate and show a superimposed image of all slices.
- Drag (Actual Size Mode): Click and drag the image to pan when in 1:1 view.
