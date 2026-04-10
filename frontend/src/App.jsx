import { useState } from 'react'
import './App.css'

function App() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [file, setFile] = useState(null)
  const [collectionName, setCollectionName] = useState('policies')
  const [uploadStatus, setUploadStatus] = useState('')

  async function handleChat(e) {
    e.preventDefault()
    if (!question.trim()) return

    setLoading(true)
    setError('')
    setAnswer('')
    setSources([])

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, collection_name: collectionName }),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Something went wrong.')
      }

      const data = await res.json()
      setAnswer(data.answer)
      setSources(data.sources)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleUpload(e) {
    e.preventDefault()
    if (!file) return

    setUploadStatus('Uploading...')

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch('/upload', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Upload failed.')
      }

      const data = await res.json()
      setCollectionName(data.collection_name)
      setUploadStatus(`Uploaded "${data.filename}" (${data.chunks_ingested} chunks). Now querying your syllabus.`)
    } catch (err) {
      setUploadStatus(`Error: ${err.message}`)
    }
  }

  return (
    <div className="app">
      <header>
        <h1>University Assistant</h1>
        <p>Ask questions about university policies or your course syllabus.</p>
      </header>

      <section className="upload-section">
        <h2>Upload a Syllabus (optional)</h2>
        <form onSubmit={handleUpload} className="upload-form">
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setFile(e.target.files[0])}
          />
          <button type="submit" disabled={!file}>
            Upload
          </button>
        </form>
        {uploadStatus && <p className="upload-status">{uploadStatus}</p>}
      </section>

      <section className="chat-section">
        <h2>Ask a Question</h2>
        <form onSubmit={handleChat} className="chat-form">
          <input
            type="text"
            placeholder="e.g. What is the policy on academic dishonesty?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <button type="submit" disabled={loading || !question.trim()}>
            {loading ? 'Thinking...' : 'Ask'}
          </button>
        </form>

        {error && <p className="error">{error}</p>}

        {answer && (
          <div className="answer">
            <h3>Answer</h3>
            <p>{answer}</p>

            {sources.length > 0 && (
              <div className="sources">
                <h4>Sources</h4>
                <ul>
                  {sources.map((s, i) => (
                    <li key={i}>
                      {s.source} — page {s.page}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  )
}

export default App
