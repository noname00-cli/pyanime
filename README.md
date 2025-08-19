# PyAnime

A text-based application to browse and watch anime.

## Installation and Usage

Follow these steps to install and run PyAnime:

1. Clone the repository:
   ```bash
   git clone https://github.com/noname00-cli/pyanime.git
   ```

2. Navigate to the project directory:
   ```bash
   cd pyanime
   ```

3. Create a virtual environment (recommended):
   - On Windows:
     ```bash
     py -m venv venv  # or python -m venv venv depending on your Python installation
     .\venv\Scripts\activate
     ```
   - On Linux/macOS:
     ```bash
     python3 -m venv venv  # or python -m venv venv depending on your Python installation
     source venv/bin/activate
     ```

4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the application:
   - On Windows:
     ```bash
     py -m bin.pyanime  # or python -m bin.pyanime depending on your Python installation
     ```
   - On Linux/macOS:
     ```bash
     python3 -m bin.pyanime  # or python -m bin.pyanime depending on your Python installation
     ```

6. If downloaded, check for
     ```file
     ~/.animecache/{anime name}/{episode name}
     ```


## Features

- Search for anime by title
- Browse anime episodes
- Download and watch episodes
- Customizable terminal interface

## UI Version

PyAnime also includes a graphical user interface. To run the UI version:

```bash
py -m bin.pyanime_ui  # On Windows (or python -m bin.pyanime_ui depending on your Python installation)
python3 -m bin.pyanime_ui  # On Linux/macOS (or python -m bin.pyanime_ui depending on your Python installation)
```

### Known Issues

The UI version may experience some glitches:

- Occasional freezing during search operations
- Display scaling issues on high-DPI screens
- Table rendering problems with certain anime titles
- Progress bar may not update correctly during downloads

If you encounter these issues, try restarting the application or switching to the text-based version.

For more information about the UI version, see [README_UI.md](README_UI.md).

As for the CLI version there are several issues like:

- Subtitles getting ahead of the audio dialog in sub
- There is no information of language in subtitle
- As for Windows users the default media player doesn't shows the subtitles
- For some anime (Example: Our Dating Story) it will leave a blank file instead of .mkv file

## Contributing

Contributions are welcome! If you'd like to contribute to PyAnime, please:

1. Fork the repository
2. Create a new branch for your feature
3. Add your changes
4. Submit a pull request

Please ensure your code follows the project's coding style and includes appropriate tests.

## Logging

PyAnime includes a comprehensive logging system. For more information, see [LOGGING.md](LOGGING.md).

## License

This project is open source and available under the MIT License.