import Header from './Header'

export default function Layout({ children }) {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main>
        {children}
      </main>
    </div>
  )
} 