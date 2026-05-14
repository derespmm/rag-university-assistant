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
  const [syllabusName, setSyllabusName] = useState('')

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
      setSyllabusName(data.filename)
      setUploadStatus(`Ingested ${data.chunks_ingested} chunks. Now querying your syllabus.`)
      setFile(null)
    } catch (err) {
      setUploadStatus(`Error: ${err.message}`)
    }
  }

  function resetToPolices() {
    setCollectionName('policies')
    setSyllabusName('')
    setUploadStatus('')
    setAnswer('')
    setSources([])
    setError('')
  }

  const queryingPolicies = collectionName === 'policies'

  return (
    <div className="app">
      <header>
        <h1>Miami University Policy Assistant</h1>
        <p>Ask questions about university policies or upload a course syllabus to query it directly.</p>
      </header>

      <section className="upload-section">
        <h2>Syllabus</h2>

        {syllabusName ? (
          <div className="syllabus-active">
            <span>Querying <strong>{syllabusName}</strong></span>
            <button className="secondary" onClick={resetToPolices}>
              Switch back to policies
            </button>
          </div>
        ) : (
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
        )}

        {uploadStatus && <p className="upload-status">{uploadStatus}</p>}
      </section>

      <section className="chat-section">
        <h2>
          Ask a Question
          {!queryingPolicies && ' (syllabus)'}
        </h2>
        <form onSubmit={handleChat} className="chat-form">
          <input
            type="text"
            placeholder={
              queryingPolicies
                ? 'e.g. What is the policy on academic dishonesty?'
                : 'e.g. When is the final exam?'
            }
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <button type="submit" disabled={loading || !question.trim()}>
            {loading ? 'Thinking…' : 'Ask'}
          </button>
        </form>

        {error && <p className="error">{error}</p>}

        {answer && (
          <div className="answer">
            <div>
              <h3>Answer</h3>
              <p className="answer-text">{answer}</p>
            </div>

            {sources.length > 0 && (
              <div className="sources">
                <h4>Sources</h4>
                <ul>
                  {sources.map((s, i) => (
                    <li key={i}>
                      {s.source} — page {s.page}, chunk {s.chunk}
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
