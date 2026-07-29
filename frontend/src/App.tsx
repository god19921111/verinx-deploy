import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { NetworkStatus } from './components/NetworkStatus'
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { ProfilePage } from './pages/ProfilePage'
import { SinglePracticePage } from './pages/SinglePracticePage'
import { FullPracticePage } from './pages/FullPracticePage'
import { HistoryPage } from './pages/HistoryPage'
import { ReportPage } from './pages/ReportPage'
import { MembershipPage } from './pages/MembershipPage'

function App() {
  return (
    <BrowserRouter>
      <NetworkStatus />
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/practice/single" element={<SinglePracticePage />} />
          <Route path="/practice/full" element={<FullPracticePage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/report/:id" element={<ReportPage />} />
          <Route path="/membership" element={<MembershipPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
