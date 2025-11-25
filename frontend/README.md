# Clipt Frontend

A React-based frontend for the Clipt web content extraction service.

## Features

- Extract web content from any URL
- Choose output format (HTML, PDF, DOCX, Markdown)
- Filter content by keywords
- Option to always include first paragraph
- Automatic file download
- Beautiful, responsive UI

## Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Backend API running on `http://localhost:5000`

## Installation

```bash
npm install
```

## Running the Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Building for Production

```bash
npm run build
```

The production-ready files will be in the `dist/` directory.

## Usage

1. Enter a URL in the "URL" field
2. Select the desired output format (HTML, PDF, DOCX, or Markdown)
3. (Optional) Enter keywords to filter paragraphs
4. (Optional) Check "Always include first paragraph" to ensure the first paragraph is included regardless of keywords
5. Click "Extract Content"
6. The processed file will be automatically downloaded

## API Endpoint

The frontend communicates with the backend API at:
```
POST http://localhost:5000/api/process
```

Make sure the backend server is running before using the frontend.

## Technologies Used

- React 18
- Vite
- CSS3 with gradient backgrounds and animations
- Fetch API for backend communication
