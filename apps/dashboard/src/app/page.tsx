import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8">Clara Engine Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Clients</CardTitle>
            <CardDescription>Manage your Twitter bot clients</CardDescription>
            <Button asChild className="mt-4">
              <Link href="/dashboard/clients">View Clients</Link>
            </Button>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Tweets</CardTitle>
            <CardDescription>Monitor and manage tweets</CardDescription>
            <Button asChild className="mt-4">
              <Link href="/dashboard/tweets">View Tweets</Link>
            </Button>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Settings</CardTitle>
            <CardDescription>Configure system settings</CardDescription>
            <Button asChild className="mt-4">
              <Link href="/dashboard/settings">View Settings</Link>
            </Button>
          </CardHeader>
        </Card>
      </div>
    </div>
  )
}
