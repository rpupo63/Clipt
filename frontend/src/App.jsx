import { useState } from 'react'
import './App.css'

function App() {
  const [url, setUrl] = useState('')
  const [filetype, setFiletype] = useState('html')
  const [keywords, setKeywords] = useState('')
  const [includeFirstParagraph, setIncludeFirstParagraph] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      // Parse keywords (comma or space separated)
      const keywordList = keywords
        .split(/[,\s]+/)
        .map(k => k.trim())
        .filter(k => k.length > 0)

      // Prepare request body
      const requestBody = {
        url: url,
        filetype: filetype,
        return_file: true
      }

      // Add optional parameters only if they have values
      if (keywordList.length > 0) {
        requestBody.keywords = keywordList
      }

      if (includeFirstParagraph) {
        requestBody.include_first_paragraph = true
      }

      // Make API request
      const response = await fetch('http://localhost:5000/api/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        // Try to get error message from response
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Server error: ${response.status}`)
      }

      // Get the file blob
      const blob = await response.blob()

      // Create download link
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl

      // Set filename based on filetype
      const filename = `clipt_output.${filetype}`
      link.download = filename

      // Trigger download
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      // Clean up
      window.URL.revokeObjectURL(downloadUrl)

      setSuccess(`Successfully downloaded ${filename}!`)
    } catch (err) {
      setError(err.message || 'An error occurred while processing the URL')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-container">
      <div className="header">
        <h1>Clipt</h1>
        <p className="subtitle">Extract and format web content with ease</p>
      </div>

      <form onSubmit={handleSubmit} className="clipt-form">
        <div className="form-group">
          <label htmlFor="url">
            URL <span className="required">*</span>
          </label>
          <input
            type="url"
            id="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/article"
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="filetype">Output Format</label>
          <select
            id="filetype"
            value={filetype}
            onChange={(e) => setFiletype(e.target.value)}
            disabled={loading}
          >
            <option value="html">HTML</option>
            <option value="pdf">PDF</option>
            <option value="docx">DOCX</option>
            <option value="md">Markdown</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="keywords">
            Keywords (optional)
          </label>
          <input
            type="text"
            id="keywords"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            placeholder="fashion, style, trend (comma or space separated)"
            disabled={loading}
          />
          <small className="help-text">
            Filter paragraphs containing these keywords
          </small>
        </div>

        <div className="form-group checkbox-group">
          <label>
            <input
              type="checkbox"
              checked={includeFirstParagraph}
              onChange={(e) => setIncludeFirstParagraph(e.target.checked)}
              disabled={loading || !keywords}
            />
            <span>Always include first paragraph</span>
          </label>
          <small className="help-text">
            Include the first paragraph even if it doesn't match keywords
          </small>
        </div>

        {error && (
          <div className="message error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {success && (
          <div className="message success-message">
            <strong>Success!</strong> {success}
          </div>
        )}

        <button
          type="submit"
          className="submit-button"
          disabled={loading || !url}
        >
          {loading ? (
            <>
              <span className="spinner"></span>
              Processing...
            </>
          ) : (
            'Extract Content'
          )}
        </button>
      </form>

      <div className="footer">
        <p>
          Powered by Clipt API • Backend running on{' '}
          <code>http://localhost:5000</code>
        </p>
      </div>
    </div>
  )
}

export default App
