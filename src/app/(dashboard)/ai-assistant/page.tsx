"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Bot,
  Send,
  User,
  Sparkles,
  TrendingUp,
  DollarSign,
  Users,
  Loader2,
  RefreshCw,
  Copy,
  ThumbsUp,
  ThumbsDown,
  Lightbulb,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

const suggestedQuestions = [
  "Who are the best available QBs under $500K NIL?",
  "Compare Travis Hunter vs Jeremiah Smith",
  "Which schools have the best portal classes?",
  "Predict the NIL value for a 4-star WR with 100K followers",
  "What's the average WAR for elite transfer QBs?",
  "Show me undervalued players in the portal",
];

const sampleResponse = `Based on the current portal data, here are the **best available quarterbacks** with NIL valuations under $500K:

| Player | School | NIL Value | WAR | Status |
|--------|--------|-----------|-----|--------|
| Marcus Williams | Oregon State | $420K | 1.4 | In Portal |
| Tyler Jackson | Memphis | $385K | 1.2 | In Portal |
| David Chen | Utah State | $290K | 0.9 | In Portal |

**Key Insights:**
- Marcus Williams led the Pac-12 in passing efficiency last season
- Tyler Jackson has strong deep ball accuracy (68% completion on 20+ yard throws)
- David Chen offers excellent value with upside

Would you like me to dive deeper into any of these players?`;

export default function AIAssistantPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Hello! I'm your Portal IQ AI Assistant. I can help you with NIL valuations, transfer portal analysis, player comparisons, and more. What would you like to know?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // Simulate API call
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: sampleResponse,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1500);
  };

  const handleSuggestedQuestion = (question: string) => {
    setInput(question);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Bot className="h-8 w-8 text-primary" />
            AI Assistant
          </h1>
          <p className="text-muted-foreground mt-1">
            Ask anything about NIL, transfers, or player analytics
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() =>
            setMessages([
              {
                id: "1",
                role: "assistant",
                content:
                  "Hello! I'm your Portal IQ AI Assistant. I can help you with NIL valuations, transfer portal analysis, player comparisons, and more. What would you like to know?",
                timestamp: new Date(),
              },
            ])
          }
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          New Chat
        </Button>
      </div>

      <div className="flex flex-1 gap-6 min-h-0">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col min-h-0">
          <Card className="glass flex-1 flex flex-col min-h-0">
            {/* Messages */}
            <ScrollArea ref={scrollRef} className="flex-1 p-4">
              <div className="space-y-6">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      "flex gap-3",
                      message.role === "user" ? "flex-row-reverse" : ""
                    )}
                  >
                    <div
                      className={cn(
                        "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                        message.role === "user"
                          ? "bg-primary"
                          : "bg-primary/20"
                      )}
                    >
                      {message.role === "user" ? (
                        <User className="h-4 w-4 text-primary-foreground" />
                      ) : (
                        <Sparkles className="h-4 w-4 text-primary" />
                      )}
                    </div>
                    <div
                      className={cn(
                        "flex-1 max-w-[80%]",
                        message.role === "user" ? "text-right" : ""
                      )}
                    >
                      <div
                        className={cn(
                          "inline-block rounded-2xl px-4 py-3 text-sm",
                          message.role === "user"
                            ? "bg-primary text-primary-foreground rounded-tr-none"
                            : "bg-card rounded-tl-none"
                        )}
                      >
                        <div
                          className={cn(
                            "prose prose-sm max-w-none",
                            message.role === "user"
                              ? "prose-invert"
                              : "prose-invert"
                          )}
                          dangerouslySetInnerHTML={{
                            __html: message.content
                              .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                              .replace(/\n/g, "<br />")
                              .replace(
                                /\|.*\|/g,
                                (match) =>
                                  `<code class="text-xs bg-background/50 px-1 rounded">${match}</code>`
                              ),
                          }}
                        />
                      </div>
                      {message.role === "assistant" && (
                        <div className="flex items-center gap-2 mt-2">
                          <Button variant="ghost" size="sm" className="h-7 px-2">
                            <Copy className="h-3 w-3 mr-1" />
                            Copy
                          </Button>
                          <Button variant="ghost" size="sm" className="h-7 px-2">
                            <ThumbsUp className="h-3 w-3" />
                          </Button>
                          <Button variant="ghost" size="sm" className="h-7 px-2">
                            <ThumbsDown className="h-3 w-3" />
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                      <Sparkles className="h-4 w-4 text-primary animate-pulse" />
                    </div>
                    <div className="bg-card rounded-2xl rounded-tl-none px-4 py-3">
                      <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>

            {/* Input Area */}
            <div className="p-4 border-t border-border">
              <div className="flex gap-2">
                <Input
                  placeholder="Ask about NIL valuations, transfers, player stats..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSend()}
                  className="bg-input border-border h-11"
                  disabled={isLoading}
                />
                <Button
                  onClick={handleSend}
                  disabled={!input.trim() || isLoading}
                  className="bg-primary text-primary-foreground hover:bg-primary/90 h-11 px-6"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="hidden lg:flex flex-col w-80 space-y-4">
          {/* Suggested Questions */}
          <Card className="glass">
            <CardContent className="p-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2 mb-3">
                <Lightbulb className="h-4 w-4 text-primary" />
                Suggested Questions
              </h3>
              <div className="space-y-2">
                {suggestedQuestions.map((question, i) => (
                  <button
                    key={i}
                    onClick={() => handleSuggestedQuestion(question)}
                    className="w-full text-left p-3 rounded-lg bg-card hover:bg-primary/10 hover:border-primary/50 border border-transparent transition-all text-sm text-muted-foreground hover:text-foreground"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Capabilities */}
          <Card className="glass">
            <CardContent className="p-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-3">
                What I Can Help With
              </h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
                    <DollarSign className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">NIL Valuations</p>
                    <p className="text-xs text-muted-foreground">Player values & projections</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
                    <Users className="h-4 w-4 text-blue-500" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">Player Comparisons</p>
                    <p className="text-xs text-muted-foreground">Side-by-side analysis</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center">
                    <TrendingUp className="h-4 w-4 text-green-500" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">Transfer Analysis</p>
                    <p className="text-xs text-muted-foreground">Portal trends & insights</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Data Sources */}
          <Card className="glass">
            <CardContent className="p-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-3">
                Powered By
              </h3>
              <div className="flex flex-wrap gap-2">
                <Badge variant="secondary">On3 NIL</Badge>
                <Badge variant="secondary">PFF Grades</Badge>
                <Badge variant="secondary">CFBD</Badge>
                <Badge variant="secondary">ESPN</Badge>
                <Badge variant="secondary">Custom Models</Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
