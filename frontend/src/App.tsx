import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import DatasetDetail from './pages/DatasetDetail'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/datasets/:id" element={<DatasetDetail />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
