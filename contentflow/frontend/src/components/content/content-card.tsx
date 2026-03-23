import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ContentItem } from "@/lib/types";

export function ContentCard({ content }: { content: ContentItem }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{content.title || "无标题"}</CardTitle>
          <Badge variant="secondary">{content.platform}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="whitespace-pre-wrap text-sm">{content.body}</p>
        {content.tags && (
          <div className="flex flex-wrap gap-1">
            {content.tags.map((tag) => (
              <Badge key={tag} variant="outline">#{tag}</Badge>
            ))}
          </div>
        )}
        {content.metadata?.cover_text != null && (
          <p className="text-sm text-muted-foreground">封面建议：{String(content.metadata.cover_text)}</p>
        )}
      </CardContent>
    </Card>
  );
}
