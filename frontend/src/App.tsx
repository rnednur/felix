import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ToastProvider } from './components/ui/toast'
import Home from './pages/Home'
import DatasetDetail from './pages/DatasetDetail'
import DatasetGroupDetail from './pages/DatasetGroupDetail'

function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/datasets/:id" element={<DatasetDetail />} />
          <Route path="/dataset-groups/:id" element={<DatasetGroupDetail />} />
          <Route path="/dataset-groups/new" element={<DatasetGroupDetail />} />
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  )
}

export default App
