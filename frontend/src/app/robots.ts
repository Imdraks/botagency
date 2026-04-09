import { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/app/", "/login", "/register", "/api/"],
      },
    ],
    sitemap: "https://radarapp.fr/sitemap.xml",
  };
}
