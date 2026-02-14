import { getInternalUsers } from '@/lib/dal'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'

export const metadata = {
  title: 'Users — HR-Plus Settings',
}

interface InternalUser {
  id: string
  user: {
    email: string
    first_name: string
    last_name: string
  }
  employee_id: string
  title: string
  is_active: boolean
  roles: { name: string }[]
}

export default async function UsersPage() {
  let users: { results: InternalUser[] } = { results: [] }

  try {
    users = await getInternalUsers()
  } catch {
    // API not available yet
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Internal Users</h2>
      </div>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Employee ID</TableHead>
              <TableHead>Title</TableHead>
              <TableHead>Roles</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.results.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground">
                  No users found. Connect the API to manage users.
                </TableCell>
              </TableRow>
            ) : (
              users.results.map((u) => (
                <TableRow key={u.id}>
                  <TableCell className="font-medium">
                    {u.user.first_name} {u.user.last_name}
                  </TableCell>
                  <TableCell>{u.user.email}</TableCell>
                  <TableCell>{u.employee_id}</TableCell>
                  <TableCell>{u.title}</TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {u.roles.map((role) => (
                        <Badge key={role.name} variant="outline">
                          {role.name}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={u.is_active ? 'default' : 'secondary'}>
                      {u.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
