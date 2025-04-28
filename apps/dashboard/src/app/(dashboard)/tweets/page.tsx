import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'

export default function TweetsPage() {
  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Tweet Management</h1>
        <div className="space-x-2">
          <Button variant="outline">Filter</Button>
          <Button variant="outline">Refresh</Button>
        </div>
      </div>

      <div className="space-y-4">
        {/* Example tweet card - will be replaced with real data */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-lg">Tech News Bot</CardTitle>
                <CardDescription className="mt-1">Posted 2 hours ago</CardDescription>
              </div>
              <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">
                Posted
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700 mb-4">
              Just in: Apple announces new MacBook Pro with M3 chip. The latest processor
              promises up to 40% faster performance than its predecessor. #Apple #Tech
            </p>
            <div className="flex justify-between items-center text-sm text-gray-500">
              <div className="space-x-4">
                <span>❤️ 45</span>
                <span>🔄 12</span>
              </div>
              <Button variant="ghost" size="sm">View on Twitter</Button>
            </div>
          </CardContent>
        </Card>

        {/* Example pending tweet */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-lg">AI Updates</CardTitle>
                <CardDescription className="mt-1">Scheduled for 3:00 PM</CardDescription>
              </div>
              <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded">
                Pending
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700 mb-4">
              Breaking: OpenAI releases GPT-4 Turbo with enhanced capabilities and
              improved performance. Stay tuned for our detailed analysis. #AI #GPT4
            </p>
            <div className="flex justify-end space-x-2">
              <Button variant="outline" size="sm">Edit</Button>
              <Button variant="outline" size="sm">Cancel</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 