export const CATEGORY_CONFIG: Record<
  string,
  { label: string; color: string; bgColor: string; icon: string }
> = {
  task: {
    label: "Task",
    color: "text-blue-400",
    bgColor: "bg-blue-500/10 border-blue-500/20",
    icon: "CheckSquare",
  },
  idea: {
    label: "Idea",
    color: "text-amber-400",
    bgColor: "bg-amber-500/10 border-amber-500/20",
    icon: "Lightbulb",
  },
  shopping: {
    label: "Shopping",
    color: "text-green-400",
    bgColor: "bg-green-500/10 border-green-500/20",
    icon: "ShoppingCart",
  },
  note: {
    label: "Note",
    color: "text-purple-400",
    bgColor: "bg-purple-500/10 border-purple-500/20",
    icon: "FileText",
  },
  meeting: {
    label: "Meeting",
    color: "text-cyan-400",
    bgColor: "bg-cyan-500/10 border-cyan-500/20",
    icon: "Users",
  },
  reflection: {
    label: "Reflection",
    color: "text-pink-400",
    bgColor: "bg-pink-500/10 border-pink-500/20",
    icon: "Heart",
  },
  contact: {
    label: "Contact",
    color: "text-orange-400",
    bgColor: "bg-orange-500/10 border-orange-500/20",
    icon: "UserPlus",
  },
  event: {
    label: "Event",
    color: "text-teal-400",
    bgColor: "bg-teal-500/10 border-teal-500/20",
    icon: "Calendar",
  },
};
