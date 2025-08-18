# PyAnime UI

A modern PyQt6-based user interface for the PyAnime downloader application.

## Features

- Modern, responsive UI with dark theme
- Search for anime by title
- View anime details and episodes
- Download individual episodes or batch download multiple episodes
- Real-time progress tracking
- Customizable appearance through CSS

## Installation

1. Make sure you have all the required dependencies installed:

```bash
pip install -r requirements.txt
```

2. Run the UI version of PyAnime:

```bash
python bin/pyanime_ui.py
```

## Customizing the UI

The UI appearance can be customized by modifying the `config/custom_style.css` file. This file contains CSS-like styling rules that control the appearance of all UI elements.

### Default Theme

The application comes with two themes:

1. **Default Theme** - A modern dark theme with blue accents (built into the application)
2. **Dracula Theme** - A popular dark theme with purple and pink accents (provided in `custom_style.css`)

### Customizing Elements

You can customize specific UI elements by modifying their properties in the CSS file. Here are some examples:

#### Changing Button Colors

```css
QPushButton {
    background-color: #ff79c6;  /* Change to your preferred color */
    color: #282a36;             /* Text color */
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #ff92d0;  /* Hover state color */
}
```

#### Changing Background Colors

```css
QMainWindow, QWidget {
    background-color: #282a36;  /* Main background color */
    color: #f8f8f2;            /* Main text color */
}

QTableWidget {
    background-color: #44475a;  /* Table background color */
    /* Other table properties */
}
```

#### Styling Specific Elements

You can target specific elements using their object names:

```css
QPushButton#search_button {
    background-color: #8be9fd;  /* Special color for search button */
    color: #282a36;
}

QLabel#anime_title_label {
    font-size: 16px;            /* Larger font for anime title */
    font-weight: bold;
    color: #bd93f9;             /* Purple color for anime title */
}
```

## UI Structure

The UI is divided into several sections:

1. **Search Bar** - Enter anime titles to search for
2. **Results Table** - Displays search results with anime titles, years, and types
3. **Episodes Table** - Shows episodes for the selected anime
4. **Log Window** - Displays application logs and messages
5. **Downloads Table** - Shows active and completed downloads with progress bars

## Development

### Adding New Features

The UI is built using PyQt6 and follows a modular design. The main components are:

- `PyAnimeUI` - The main window class
- `DownloadWorker` - Thread for handling downloads
- `SearchWorker` - Thread for handling anime searches
- `EpisodeWorker` - Thread for loading episode data

To add new features, you can extend these classes or create new worker threads for additional functionality.

### Styling Guidelines

When adding new UI elements, follow these guidelines for consistent styling:

1. Use the existing color palette for consistency
2. Set object names for important widgets to allow CSS targeting
3. Use layouts for proper resizing behavior
4. Add new style rules to the CSS file for custom elements

## Troubleshooting

### Common Issues

- **UI not loading**: Make sure PyQt6 is installed correctly
- **Custom styles not applying**: Check that the CSS file is in the correct location
- **Download errors**: Check the log window for detailed error messages

### Logs

The application logs are displayed in the log window and are also written to `pyanime.log` in the application directory.