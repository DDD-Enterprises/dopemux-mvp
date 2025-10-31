import { Navbar } from '@/components/layout/navbar'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { useTheme } from 'next-themes'
import { useState } from 'react'
import { Toaster, toast } from 'sonner'

export default function Home() {
  const [theme, setTheme] = useState('system')
  const [expanded, setExpanded] = useState(false)
  const [radioValue, setRadioValue] = useState('option1')

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(newTheme)
    toast.success(`Theme switched to ${newTheme}`)
  }

  const handleError = () => {
    try {
      // Simulate error
      throw new Error('Demo error')
    } catch (error) {
      toast.error('An error occurred!', {
        action: {
          label: 'Retry',
          onClick: () => toast.success('Retry clicked!'),
        },
      })
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar />
      <main className="container mx-auto p-4">
        <Card>
          <CardHeader>
            <CardTitle>Dopemux Ultra UI Demo</CardTitle>
            <CardDescription>ADHD-Optimized Tmux Dashboard</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Dark Mode Toggle */}
            <div className="flex items-center justify-between">
              <label>Dark Mode</label>
              <Button onClick={toggleTheme}>Toggle</Button>
            </div>

            {/* Collapsible Section */}
            <Accordion type="single" collapsible value={expanded ? 'item-1' : ''}>
              <AccordionItem value="item-1">
                <AccordionTrigger>Collapsible Logs (Click to Expand)</AccordionTrigger>
                <AccordionContent className="max-h-32 overflow-y-auto">
                  <p>Log line 1: System healthy</p>
                  <p>Log line 2: Agent active</p>
                  <p>Log line 3: Build complete</p>
                  <p>Log line 4: Test passed</p>
                  <p>Log line 5: All systems go</p>
                </AccordionContent>
              </AccordionItem>
            </Accordion>

            {/* Radio Group */}
            <div>
              <label>Agent Selection</label>
              <RadioGroup value={radioValue} onValueChange={setRadioValue}>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="option1" id="option1" />
                  <label htmlFor="option1">Option 1</label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="option2" id="option2" />
                  <label htmlFor="option2">Option 2</label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="option3" id="option3" />
                  <label htmlFor="option3">Option 3</label>
                </div>
              </RadioGroup>
            </div>

            {/* Real-Time Status (Simulated) */}
            <div className="space-y-2">
              <h3>Status Indicators</h3>
              <div className="flex items-center justify-between">
                <span>MCP Servers</span>
                <Badge variant="default">Healthy</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Agents</span>
                <Badge variant="outline">2 Active</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Build</span>
                <Progress value={100} className="w-full" />
              </div>
            </div>

            {/* Error Handling Demo */}
            <Button onClick={handleError} variant="destructive">
              Simulate Error (Demo)
            </Button>
          </CardContent>
        </Card>
      </main>
      <Toaster />
    </div>
  )
}