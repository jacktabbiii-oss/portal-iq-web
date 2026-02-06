"use client";

import { useState, useRef, useEffect, useCallback } from "react";
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
  AlertCircle,
  CheckCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { searchAI, getSearchStatus, type SearchStatusResponse } from "@/lib/api/search";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  sources?: string[];
  error?: boolean;
}

const suggestedQuestions = [
  "Who are the best available QBs under $500K NIL?",
  "Compare Travis Hunter vs Jeremiah Smith",
  "Which schools have the best portal classes?",
  "Predict the NIL value for a 4-star WR with 100K followers",
  "What's the average WAR for elite transfer QBs?",
  "Show me undervalued players in the portal",
];

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
  const [aiStatus, setAIStatus] = useState<SearchStatusResponse | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Check AI status on mount
  useEffect(() => {
    const checkStatus = async () => {
      setStatusLoading(true);
      try {
        const status = await getSearchStatus();
        setAIStatus(status);
      } catch (error) {
        console.error("Failed to check AI status:", error);
        setAIStatus(null);
      } finally {
        setStatusLoading(false);
      }
    };
    checkStatus();
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = useCallback(async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const query = input.trim();
    setInput("");
    setIsLoading(true);

    try {
      // Build context from recent messages
      const recentMessages = messages.slice(-4).map(m => `${m.role}: ${m.content}`).join("\n");

      const response = await searchAI(query, recentMessages);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.response || "I couldn't find relevant information for your query. Please try rephrasing or asking about specific players, teams, or NIL values.",
        timestamp: new Date(),
        sources: response.sources,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("AI search error:", error);

      // Check if it's a connection error or API error
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      const isConnectionError = errorMessage.includes("Network") || errorMessage.includes("fetch");

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: isConnectionError
          ? "I'm having trouble connecting to the server. Please check that the API is running and try again."
          : `I encountered an error processing your request: ${errorMessage}. Please try again or rephrase your question.`,
        timestamp: new Date(),
        error: true,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, messages]);

  const handleSuggestedQuestion = (question: string) => {
    setInput(question);
  };

  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content);
  };

  const handleNewChat = () => {
    setMessages([
      {
        id: "1",
        role: "assistant",
        content:
          "Hello! I'm your Portal IQ AI Assistant. I can help you with NIL valuations, transfer portal analysis, player comparisons, and more. What would you like to know?",
        timestamp: new Date(),
      },
    ]);
  };

  // Simple markdown-like formatting
  const formatContent = (content: string) => {
    return content
      .replace(/\*\*(.*?)\*\*/g, "<strong class='text-primary'>$1</strong>")
      .replace(/\n\n/g, "</p><p class='mb-2'>")
      .replace(/\n/g, "<br />")
      .replace(/\|(.*?)\|/g, (match) => {
        // Table handling
        const cells = match.split("|").filter(Boolean);
        if (cells.every(c => c.trim() === "---" || c.trim().match(/^-+$/))) {
          return ""; // Skip header separator
        }
        return `<span class="inline-block bg-muted/50 px-2 py-0.5 rounded text-xs font-mono">${cells.join(" | ")}</span>`;
      });
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
        <div className="flex items-center gap-2">
          {/* Status indicator */}
          {statusLoading ? (
            <Badge variant="secondary" className="gap-1">
              <Loader2 className="h-3 w-3 animate-spin" />
              Checking...
            </Badge>
          ) : aiStatus?.available ? (
            <Badge variant="secondary" className="gap-1 bg-green-500/20 text-green-500 border-green-500/50">
              <CheckCircle className="h-3 w-3" />
              AI Ready
            </Badge>
          ) : (
            <Badge variant="secondary" className="gap-1 bg-yellow-500/20 text-yellow-500 border-yellow-500/50">
              <AlertCircle className="h-3 w-3" />
              Limited Mode
            </Badge>
          )}
          <Button variant="outline" size="sm" onClick={handleNewChat}>
            <RefreshCw className="h-4 w-4 mr-2" />
            New Chat
          </Button>
        </div>
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
                          : message.error
                          ? "bg-red-500/20"
                          : "bg-primary/20"
                      )}
                    >
                      {message.role === "user" ? (
                        <User className="h-4 w-4 text-primary-foreground" />
                      ) : message.error ? (
                        <AlertCircle className="h-4 w-4 text-red-500" />
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
                            : message.error
                            ? "bg-red-500/10 border border-red-500/30 rounded-tl-none"
                            : "bg-card rounded-tl-none"
                        )}
                      >
                        <div
                          className="prose prose-sm max-w-none prose-invert"
                          dangerouslySetInnerHTML={{
                            __html: `<p class="mb-2">${formatContent(message.content)}</p>`,
                          }}
                        />
                        {message.sources && message.sources.length > 0 && (
                          <div className="mt-2 pt-2 border-t border-border">
                            <p className="text-xs text-muted-foreground mb-1">Sources:</p>
                            <div className="flex flex-wrap gap-1">
                              {message.sources.map((source, i) => (
                                <Badge key={i} variant="outline" className="text-xs">
                                  {source}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      {message.role === "assistant" && !message.error && (
                        <div className="flex items-center gap-2 mt-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 px-2"
                            onClick={() => handleCopy(message.content)}
                          >
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
                      <div className="flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Thinking...</span>
                      </div>
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
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
                  className="bg-input border-border h-11"
                  disabled={isLoading}
                />
                <Button
                  onClick={handleSend}
                  disabled={!input.trim() || isLoading}
                  className="bg-primary text-primary-foreground hover:bg-primary/90 h-11 px-6"
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
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

          {/* Powered By */}
          <Card className="glass">
            <CardContent className="p-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-3">
                Powered By
              </h3>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-primary/20 rounded-lg flex items-center justify-center">
                  <span className="text-lg">🧭</span>
                </div>
                <div>
                  <p className="font-bold text-primary">Elite Sports Solutions</p>
                  <p className="text-xs text-muted-foreground">
                    Proprietary AI & Analytics
                  </p>
                </div>
              </div>
              {aiStatus && (
                <p className="text-xs text-muted-foreground mt-3">
                  {aiStatus.datasets_loaded} datasets loaded
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
