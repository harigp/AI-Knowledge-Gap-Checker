import React from 'react';
import { Header } from './components/layout';
import { Card, Badge, Button } from './components/common';

export function App() {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* 1. Render Navigation Header */}
      <Header currentStep="upload" />

      {/* 2. Main Content Playground */}
      <main className="max-w-4xl mx-auto p-8 space-y-6">
        <Card>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-slate-800">Phase 1 UI Component Check</h2>
              <Badge variant="green">Component Active</Badge>
            </div>
            
            <p className="text-slate-600">
              Your custom UI shell, card wrapper, status badges, and interactive buttons are working!
            </p>

            {/* Test Status Badges */}
            <div className="flex gap-2 items-center pt-2">
              <span className="text-xs font-semibold text-slate-500">Badge Variants:</span>
              <Badge variant="green">Strong</Badge>
              <Badge variant="yellow">Developing</Badge>
              <Badge variant="red">Weak</Badge>
              <Badge variant="gray">Unassessed</Badge>
            </div>

            {/* Test Action Buttons */}
            <div className="flex gap-3 pt-4 border-t border-slate-100">
              <Button variant="primary" onClick={() => alert("Primary button clicked!")}>
                Primary Action
              </Button>
              <Button variant="outline">
                Secondary Action
              </Button>
              <Button variant="primary" isLoading>
                Loading State
              </Button>
            </div>
          </div>
        </Card>
      </main>
    </div>
  );
}

export default App;
