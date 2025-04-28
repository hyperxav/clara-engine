import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export default function SettingsPage() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Settings</h1>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>API Configuration</CardTitle>
            <CardDescription>Configure your API endpoints and keys</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="api-url">API URL</Label>
                <Input
                  id="api-url"
                  placeholder="https://api.example.com"
                  defaultValue="https://api.clara-engine.com"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="api-key">API Key</Label>
                <Input
                  id="api-key"
                  type="password"
                  placeholder="Enter your API key"
                />
              </div>
              <Button>Save Changes</Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Rate Limits</CardTitle>
            <CardDescription>Configure rate limits for tweet generation and posting</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="tweets-per-hour">Tweets per Hour</Label>
                <Input
                  id="tweets-per-hour"
                  type="number"
                  placeholder="Enter tweets per hour limit"
                  defaultValue="10"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="openai-tokens">OpenAI Tokens per Minute</Label>
                <Input
                  id="openai-tokens"
                  type="number"
                  placeholder="Enter token limit per minute"
                  defaultValue="3000"
                />
              </div>
              <Button>Update Limits</Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System Status</CardTitle>
            <CardDescription>View and manage system status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Engine Status</span>
                <span className="text-green-600 font-medium">Running</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Active Clients</span>
                <span className="font-medium">12</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Pending Tweets</span>
                <span className="font-medium">5</span>
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline">Restart Engine</Button>
                <Button variant="outline">Clear Cache</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 