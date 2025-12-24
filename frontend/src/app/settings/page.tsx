"use client";

import { AppLayout, ProtectedRoute } from "@/components/layout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuthStore } from "@/store/auth";
import { Bell, User, Lock, Palette, LayoutDashboard, Calendar, Bookmark } from "lucide-react";
import { NotificationSettings } from "@/components/settings/NotificationSettings";
import { DashboardCustomizer } from "@/components/settings/DashboardCustomizer";
import { GoogleCalendarIntegration } from "@/components/settings/GoogleCalendarIntegration";
import { TwoFactorSettings } from "@/components/settings/TwoFactorSettings";
import { ThemeToggle } from "@/components/ui/theme-toggle";

function SettingsContent() {
  const { user } = useAuthStore();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Paramètres</h1>
        <p className="text-muted-foreground">
          Gérez votre compte et vos préférences
        </p>
      </div>

      <Tabs defaultValue="profile" className="space-y-4">
        <TabsList className="flex-wrap h-auto gap-1">
          <TabsTrigger value="profile">
            <User className="h-4 w-4 mr-2" />
            Profil
          </TabsTrigger>
          <TabsTrigger value="notifications">
            <Bell className="h-4 w-4 mr-2" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="dashboard">
            <LayoutDashboard className="h-4 w-4 mr-2" />
            Dashboard
          </TabsTrigger>
          <TabsTrigger value="calendar">
            <Calendar className="h-4 w-4 mr-2" />
            Calendrier
          </TabsTrigger>
          <TabsTrigger value="security">
            <Lock className="h-4 w-4 mr-2" />
            Sécurité
          </TabsTrigger>
          <TabsTrigger value="appearance">
            <Palette className="h-4 w-4 mr-2" />
            Apparence
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile">
          <Card>
            <CardHeader>
              <CardTitle>Informations du profil</CardTitle>
              <CardDescription>
                Mettez à jour vos informations personnelles
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" defaultValue={user?.email} disabled />
              </div>
              <div className="space-y-2">
                <Label htmlFor="full_name">Nom complet</Label>
                <Input id="full_name" defaultValue={user?.full_name || ""} />
              </div>
              <Button>Enregistrer</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications">
          <NotificationSettings />
        </TabsContent>

        <TabsContent value="dashboard">
          <DashboardCustomizer />
        </TabsContent>

        <TabsContent value="calendar">
          <GoogleCalendarIntegration />
        </TabsContent>

        <TabsContent value="security">
          <div className="space-y-6">
            <TwoFactorSettings />
            
            <Card>
              <CardHeader>
                <CardTitle>Mot de passe</CardTitle>
                <CardDescription>
                  Changez votre mot de passe
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="current_password">Mot de passe actuel</Label>
                  <Input id="current_password" type="password" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="new_password">Nouveau mot de passe</Label>
                  <Input id="new_password" type="password" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirm_password">Confirmer le nouveau mot de passe</Label>
                  <Input id="confirm_password" type="password" />
                </div>
                <Button>Changer le mot de passe</Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="appearance">
          <Card>
            <CardHeader>
              <CardTitle>Apparence</CardTitle>
              <CardDescription>
                Personnalisez l&apos;interface
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Thème</p>
                  <p className="text-sm text-muted-foreground">
                    Choisir le thème de l&apos;application
                  </p>
                </div>
                <ThemeToggle />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Affichage compact</p>
                  <p className="text-sm text-muted-foreground">
                    Réduire l&apos;espacement dans les listes
                  </p>
                </div>
                <Switch />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <ProtectedRoute>
      <AppLayout>
        <SettingsContent />
      </AppLayout>
    </ProtectedRoute>
  );
}
