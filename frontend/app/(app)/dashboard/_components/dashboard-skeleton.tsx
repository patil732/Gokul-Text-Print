"use client";

import * as React from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardHeader, CardContent } from "@/components/ui/card";

export function DashboardSkeleton() {
  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto animate-pulse">
      {/* Header Skeleton */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Skeleton className="w-8 h-8 rounded-lg" />
            <Skeleton className="w-48 h-7 rounded-md" />
            <Skeleton className="w-20 h-5 rounded-full" />
          </div>
          <Skeleton className="w-80 h-4 rounded-md" />
        </div>
        <div className="flex items-center gap-2">
          <Skeleton className="w-28 h-9 rounded-lg" />
          <Skeleton className="w-32 h-9 rounded-lg" />
        </div>
      </div>

      {/* Alert Banner Skeleton */}
      <Skeleton className="w-full h-14 rounded-xl" />

      {/* 4 Summary Cards Skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="bg-card border-border">
            <CardHeader className="pb-2 space-y-2">
              <Skeleton className="w-28 h-3.5 rounded-sm" />
              <div className="flex items-center justify-between">
                <Skeleton className="w-32 h-8 rounded-md" />
                <Skeleton className="w-16 h-5 rounded-full" />
              </div>
            </CardHeader>
            <CardContent className="pt-0 space-y-1">
              <Skeleton className="w-full h-3 rounded-sm" />
              <Skeleton className="w-24 h-3 rounded-sm" />
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Chart Section Skeleton */}
      <Card className="bg-card border-border">
        <CardHeader className="flex flex-row items-center justify-between pb-4">
          <div className="space-y-2">
            <Skeleton className="w-48 h-5 rounded-md" />
            <Skeleton className="w-72 h-3.5 rounded-sm" />
          </div>
          <Skeleton className="w-36 h-8 rounded-lg" />
        </CardHeader>
        <CardContent>
          <Skeleton className="w-full h-72 rounded-xl" />
        </CardContent>
      </Card>

      {/* Two-Column Activity & Recommendations Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-card border-border">
          <CardHeader className="space-y-2">
            <Skeleton className="w-40 h-5 rounded-md" />
            <Skeleton className="w-60 h-3.5 rounded-sm" />
          </CardHeader>
          <CardContent className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex items-start gap-3 p-2.5 rounded-lg border border-border/40">
                <Skeleton className="w-8 h-8 rounded-lg shrink-0" />
                <div className="space-y-1.5 flex-1">
                  <Skeleton className="w-3/4 h-4 rounded-sm" />
                  <Skeleton className="w-1/2 h-3 rounded-sm" />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader className="space-y-2">
            <Skeleton className="w-44 h-5 rounded-md" />
            <Skeleton className="w-64 h-3.5 rounded-sm" />
          </CardHeader>
          <CardContent className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-3 rounded-xl border border-border/60 space-y-2">
                <div className="flex items-center justify-between">
                  <Skeleton className="w-32 h-4 rounded-sm" />
                  <Skeleton className="w-16 h-4 rounded-full" />
                </div>
                <Skeleton className="w-full h-3 rounded-sm" />
                <Skeleton className="w-4/5 h-3 rounded-sm" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
