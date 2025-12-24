"use client";

import { useState } from "react";
import {
  User,
  Building,
  Hash,
  Mail,
  Phone,
  Globe,
  ExternalLink,
  Calendar,
  Star,
  CheckCircle,
  AlertCircle,
  Clock,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { formatRelativeDate } from "@/lib/utils";

// Types
interface ContactRanked {
  type: string;
  value: string;
  label?: string;
  reliability_score: number;
  source?: string;
  is_verified?: boolean;
}

interface UsefulFact {
  fact: string;
  source?: string;
  category?: string;
}

interface TimelineEvent {
  date?: string;
  event_type: string;
  description: string;
  source?: string;
}

interface SourceUsed {
  name: string;
  url?: string;
  document_count: number;
}

export interface Brief {
  id: string;
  entity_id: string;
  entity_name?: string;
  entity_type?: "PERSON" | "ORGANIZATION" | "TOPIC";
  objective: string;
  timeframe_days: number;
  overview?: string;
  contacts_ranked: ContactRanked[];
  useful_facts: UsefulFact[];
  timeline: TimelineEvent[];
  sources_used: SourceUsed[];
  document_count: number;
  contact_count: number;
  completeness_score: number;
  generated_at: string;
}

// Icons for contact types
const CONTACT_ICONS: Record<string, typeof Mail> = {
  EMAIL: Mail,
  PHONE: Phone,
  BOOKING: Calendar,
  PRESS: Globe,
  AGENT: User,
  MANAGEMENT: Building,
  SOCIAL: Globe,
  FORM: Globe,
};

// Icons for entity types
const ENTITY_ICONS: Record<string, typeof User> = {
  PERSON: User,
  ORGANIZATION: Building,
  TOPIC: Hash,
};

// Objective labels
const OBJECTIVE_LABELS: Record<string, string> = {
  SPONSOR: "Sponsor / Partenariat",
  BOOKING: "Booking",
  PRESS: "Presse",
  VENUE: "Lieu / Salle",
  SUPPLIER: "Prestataires",
  GRANT: "Subventions",
};

// Event type colors
const EVENT_COLORS: Record<string, string> = {
  CONCERT: "bg-purple-100 text-purple-800",
  RELEASE: "bg-blue-100 text-blue-800",
  COLLABORATION: "bg-green-100 text-green-800",
  ANNOUNCEMENT: "bg-yellow-100 text-yellow-800",
  AWARD: "bg-amber-100 text-amber-800",
  INTERVIEW: "bg-pink-100 text-pink-800",
};

interface BriefCardProps {
  brief: Brief;
  onEntityClick?: (entityId: string) => void;
  expanded?: boolean;
}

export function BriefCard({ brief, onEntityClick, expanded = false }: BriefCardProps) {
  const [isExpanded, setIsExpanded] = useState(expanded);
  const [copiedContact, setCopiedContact] = useState<string | null>(null);
  
  const EntityIcon = ENTITY_ICONS[brief.entity_type || "PERSON"] || User;
  
  const getReliabilityColor = (score: number) => {
    if (score >= 5) return "text-green-600";
    if (score >= 2) return "text-blue-600";
    if (score >= 0) return "text-yellow-600";
    return "text-red-600";
  };
  
  const getReliabilityLabel = (score: number) => {
    if (score >= 5) return "Très fiable";
    if (score >= 2) return "Fiable";
    if (score >= 0) return "À vérifier";
    return "Non fiable";
  };
  
  const copyContact = async (value: string) => {
    await navigator.clipboard.writeText(value);
    setCopiedContact(value);
    setTimeout(() => setCopiedContact(null), 2000);
  };
  
  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <EntityIcon className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle 
                className="text-lg cursor-pointer hover:text-primary transition-colors"
                onClick={() => onEntityClick?.(brief.entity_id)}
              >
                {brief.entity_name || "Entité inconnue"}
              </CardTitle>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="outline" className="text-xs">
                  {OBJECTIVE_LABELS[brief.objective] || brief.objective}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {brief.timeframe_days}j • {brief.document_count} doc(s)
                </span>
              </div>
            </div>
          </div>
          
          {/* Completeness score */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <div className="text-right">
                  <div className="flex items-center gap-1">
                    {brief.completeness_score >= 0.7 ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : brief.completeness_score >= 0.4 ? (
                      <Clock className="h-4 w-4 text-yellow-600" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-red-600" />
                    )}
                    <span className="text-sm font-medium">
                      {Math.round(brief.completeness_score * 100)}%
                    </span>
                  </div>
                  <Progress 
                    value={brief.completeness_score * 100} 
                    className="w-16 h-1.5 mt-1" 
                  />
                </div>
              </TooltipTrigger>
              <TooltipContent>
                Score de complétude du dossier
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Overview */}
        {brief.overview && (
          <div className="text-sm text-muted-foreground">
            {brief.overview.length > 200 && !isExpanded
              ? `${brief.overview.slice(0, 200)}...`
              : brief.overview}
          </div>
        )}
        
        {/* Contacts - Always visible */}
        {brief.contacts_ranked.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold flex items-center gap-2">
              <Mail className="h-4 w-4" />
              Contacts ({brief.contact_count})
            </h4>
            <div className="grid gap-2">
              {brief.contacts_ranked.slice(0, isExpanded ? undefined : 3).map((contact, i) => {
                const ContactIcon = CONTACT_ICONS[contact.type] || Mail;
                return (
                  <div 
                    key={i} 
                    className="flex items-center justify-between p-2 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <ContactIcon className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{contact.value}</p>
                        {contact.label && (
                          <p className="text-xs text-muted-foreground truncate">{contact.label}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger>
                            <div className={`flex items-center gap-1 ${getReliabilityColor(contact.reliability_score)}`}>
                              <Star className="h-3 w-3" />
                              <span className="text-xs font-medium">
                                {contact.reliability_score > 0 ? "+" : ""}{contact.reliability_score}
                              </span>
                            </div>
                          </TooltipTrigger>
                          <TooltipContent>
                            {getReliabilityLabel(contact.reliability_score)}
                            {contact.source && ` • Source: ${contact.source}`}
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                      
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => copyContact(contact.value)}
                      >
                        {copiedContact === contact.value ? (
                          <Check className="h-3 w-3 text-green-600" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
        
        {/* Expandable sections */}
        <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
          <CollapsibleContent className="space-y-4">
            {/* Useful Facts */}
            {brief.useful_facts.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-semibold">Infos utiles</h4>
                <ul className="space-y-1">
                  {brief.useful_facts.map((fact, i) => (
                    <li key={i} className="text-sm flex items-start gap-2">
                      <span className="text-primary mt-1">•</span>
                      <span>
                        {fact.fact}
                        {fact.source && (
                          <span className="text-xs text-muted-foreground ml-1">
                            ({fact.source})
                          </span>
                        )}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {/* Timeline */}
            {brief.timeline.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-semibold flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  Événements récents
                </h4>
                <div className="space-y-2">
                  {brief.timeline.slice(0, 5).map((event, i) => (
                    <div 
                      key={i} 
                      className="flex items-start gap-3 text-sm"
                    >
                      <Badge 
                        variant="secondary" 
                        className={`${EVENT_COLORS[event.event_type] || "bg-gray-100"} text-xs flex-shrink-0`}
                      >
                        {event.date || "Récent"}
                      </Badge>
                      <span className="text-muted-foreground">{event.description}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Sources */}
            {brief.sources_used.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-semibold">Sources utilisées</h4>
                <div className="flex flex-wrap gap-2">
                  {brief.sources_used.map((source, i) => (
                    <Badge key={i} variant="outline" className="text-xs gap-1">
                      {source.name}
                      <span className="text-muted-foreground">({source.document_count})</span>
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CollapsibleContent>
          
          <CollapsibleTrigger asChild>
            <Button variant="ghost" size="sm" className="w-full mt-2">
              {isExpanded ? (
                <>
                  <ChevronUp className="h-4 w-4 mr-1" />
                  Réduire
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4 mr-1" />
                  Voir plus ({brief.useful_facts.length} infos, {brief.timeline.length} événements)
                </>
              )}
            </Button>
          </CollapsibleTrigger>
        </Collapsible>
        
        {/* Footer */}
        <div className="flex items-center justify-between pt-2 border-t text-xs text-muted-foreground">
          <span>
            Généré {formatRelativeDate(brief.generated_at)}
          </span>
          {brief.contacts_ranked.length === 0 && (
            <Badge variant="outline" className="text-xs">
              Aucun contact fiable trouvé
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default BriefCard;
