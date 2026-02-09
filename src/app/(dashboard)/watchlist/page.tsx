"use client";

import Image from "next/image";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Users,
  Download,
  Trash2,
  Star,
  DollarSign,
  ArrowRightLeft,
  Heart,
  FileText,
} from "lucide-react";
import { useWatchlist } from "@/hooks/use-watchlist";
import { useState, useEffect } from "react";

function formatCurrency(value: number | undefined | null): string {
  if (value == null || isNaN(value)) return "$0";
  if (value >= 1000000000) {
    return `$${(value / 1000000000).toFixed(1)}B`;
  } else if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}K`;
  }
  return `$${value.toLocaleString()}`;
}

export default function WatchlistPage() {
  const { watchlist, removeFromWatchlist, isLoaded } = useWatchlist();
  const [notes, setNotes] = useState<Record<string, string>>({});

  // Load notes from localStorage on mount
  useEffect(() => {
    const savedNotes = localStorage.getItem("portaliq_watchlist_notes");
    if (savedNotes) {
      try {
        setNotes(JSON.parse(savedNotes));
      } catch {
        console.error("Failed to parse notes");
      }
    }
  }, []);

  const updateNote = (playerId: string, note: string) => {
    const updated = { ...notes, [playerId]: note };
    setNotes(updated);
    localStorage.setItem("portaliq_watchlist_notes", JSON.stringify(updated));
  };

  const exportWatchlist = () => {
    const data = watchlist.map((p) => ({
      ...p,
      notes: notes[p.id] || "",
    }));
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "portaliq_watchlist.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportCSV = () => {
    const headers = ["Name", "Position", "School", "NIL Value", "Stars", "Added Date", "Notes"];
    const rows = watchlist.map((p) => [
      p.player_name,
      p.position,
      p.school,
      p.nil_valuation,
      p.stars || "",
      new Date(p.added_date).toLocaleDateString(),
      notes[p.id] || "",
    ]);
    const csv = [headers, ...rows].map((row) => row.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "portaliq_watchlist.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!isLoaded) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading watchlist...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Heart className="h-8 w-8 text-primary" />
            Watchlist
          </h1>
          <p className="text-muted-foreground mt-1">
            Track and manage players you&apos;re interested in
          </p>
        </div>
        {watchlist.length > 0 && (
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={exportCSV}>
              <FileText className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
            <Button variant="outline" size="sm" onClick={exportWatchlist}>
              <Download className="h-4 w-4 mr-2" />
              Export JSON
            </Button>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="glass">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
                <Users className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase">Total Players</p>
                <p className="text-2xl font-bold">{watchlist.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                <DollarSign className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase">Total NIL Value</p>
                <p className="text-2xl font-bold">
                  {formatCurrency(watchlist.reduce((sum, p) => sum + (p.nil_valuation || 0), 0))}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                <Star className="h-5 w-5 text-yellow-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase">Avg Stars</p>
                <p className="text-2xl font-bold">
                  {watchlist.length > 0 && watchlist.filter((p) => p.stars).length > 0
                    ? (
                        watchlist.filter((p) => p.stars).reduce((sum, p) => sum + (p.stars || 0), 0) /
                        watchlist.filter((p) => p.stars).length
                      ).toFixed(1)
                    : "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <DollarSign className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase">Avg NIL</p>
                <p className="text-2xl font-bold">
                  {watchlist.length > 0
                    ? formatCurrency(
                        watchlist.reduce((sum, p) => sum + (p.nil_valuation || 0), 0) / watchlist.length
                      )
                    : "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Watchlist Table or Empty State */}
      {watchlist.length === 0 ? (
        <Card className="glass">
          <CardContent className="p-12 text-center">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
              <Heart className="h-8 w-8 text-primary" />
            </div>
            <h2 className="text-xl font-bold mb-2">Your watchlist is empty</h2>
            <p className="text-muted-foreground mb-6 max-w-md mx-auto">
              Add players from the Portal Intelligence or NIL Valuator pages to track them here.
            </p>
            <div className="flex justify-center gap-4">
              <Button asChild className="bg-primary text-primary-foreground">
                <Link href="/portal-intelligence">
                  <ArrowRightLeft className="h-4 w-4 mr-2" />
                  Browse Portal
                </Link>
              </Button>
              <Button asChild variant="outline">
                <Link href="/nil-valuator">
                  <DollarSign className="h-4 w-4 mr-2" />
                  NIL Valuator
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="glass overflow-hidden">
          <CardHeader className="border-b border-border bg-primary/5 px-6 py-4">
            <CardTitle className="text-sm font-bold uppercase tracking-wider flex items-center justify-between">
              <span>Your Players</span>
              <Badge variant="secondary">{watchlist.length} players</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-border">
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground w-16"></TableHead>
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Player</TableHead>
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Pos</TableHead>
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">School</TableHead>
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-center">Stars</TableHead>
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-right">NIL Value</TableHead>
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Notes</TableHead>
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-center">Added</TableHead>
                  <TableHead className="w-10"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {watchlist.map((player) => (
                  <TableRow key={player.id} className="border-border">
                    <TableCell>
                      {player.headshot_url ? (
                        <Image
                          src={player.headshot_url}
                          alt={player.player_name}
                          width={40}
                          height={40}
                          className="rounded-full object-cover"
                          unoptimized
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                          <span className="text-xs font-bold text-primary">
                            {player.player_name?.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                          </span>
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="font-semibold">{player.player_name}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-mono text-xs">
                        {player.position}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{player.school}</TableCell>
                    <TableCell className="text-center">
                      {player.stars ? (
                        <div className="flex justify-center text-yellow-500">
                          {Array.from({ length: Math.min(player.stars, 5) }).map((_, i) => (
                            <Star key={i} className="h-3 w-3 fill-yellow-500" />
                          ))}
                        </div>
                      ) : (
                        "—"
                      )}
                    </TableCell>
                    <TableCell className="text-right font-bold text-primary">
                      {formatCurrency(player.nil_valuation)}
                    </TableCell>
                    <TableCell className="max-w-[200px]">
                      <Textarea
                        value={notes[player.id] || ""}
                        onChange={(e) => updateNote(player.id, e.target.value)}
                        placeholder="Add notes..."
                        className="min-h-[60px] text-xs bg-input resize-none"
                      />
                    </TableCell>
                    <TableCell className="text-center text-xs text-muted-foreground">
                      {new Date(player.added_date).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-red-500 hover:text-red-400 hover:bg-red-500/10"
                        onClick={() => removeFromWatchlist(player.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
