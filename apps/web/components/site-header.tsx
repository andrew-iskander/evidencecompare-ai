"use client";

import Link from "next/link";
import { Activity, LogOut } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import { useAuth } from "@/components/auth-provider";
import { buttonVariants, Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function SiteHeader() {
  const { user, ready, logout } = useAuth();

  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <span className="grid size-8 place-items-center rounded-md bg-primary text-primary-foreground">
            <Activity className="size-5" />
          </span>
          <span className="tracking-tight">
            EvidenceCompare<span className="text-primary"> AI</span>
          </span>
        </Link>

        <nav className="flex items-center gap-1 sm:gap-2">
          {ready && user ? (
            <>
              <Link
                href="/reports"
                className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}
              >
                My reports
              </Link>
              <Link
                href="/compare"
                className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}
              >
                New comparison
              </Link>
              <span className="hidden text-sm text-muted-foreground sm:inline">
                {user.email}
              </span>
              <Button
                variant="ghost"
                size="icon"
                aria-label="Sign out"
                onClick={logout}
              >
                <LogOut className="size-5" />
              </Button>
            </>
          ) : (
            <Link
              href="/login"
              className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}
            >
              Sign in
            </Link>
          )}
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
