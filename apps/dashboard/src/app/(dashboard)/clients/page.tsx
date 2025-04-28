import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'

export default function ClientsPage() {
  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Twitter Bot Clients</h1>
        <Button>Add New Client</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Example client card - will be replaced with real data */}
        <Card>
          <CardHeader>
            <CardTitle>Tech News Bot</CardTitle>
            <CardDescription>Posts about latest tech news and updates</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Status:</span>
                <span className="font-medium text-green-600">Active</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Last Tweet:</span>
                <span className="font-medium">2 hours ago</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Tweet Count:</span>
                <span className="font-medium">1,234</span>
              </div>
            </div>
            <div className="mt-4 space-x-2">
              <Button variant="outline" size="sm">Edit</Button>
              <Button variant="outline" size="sm">View Tweets</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 